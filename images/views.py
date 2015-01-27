from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms import ValidationError
from django.forms.models import model_to_dict
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.conf import settings

from userena.models import User
from annotations.forms import AnnotationAreaPercentsForm
from annotations.model_utils import AnnotationAreaUtils
from annotations.models import LabelGroup, Label, LabelSet
from annotations.utils import image_annotation_area_is_editable, image_has_any_human_annotations
from decorators import source_permission_required, image_visibility_required, image_permission_required, source_visibility_required

from images.models import Source, Image, SourceInvite
from images.tasks import *
from images.forms import *
from images.model_utils import PointGen
from images.utils import *
from lib.utils import get_map_sources
import json , csv, os.path, time, datetime
from numpy import array
from visualization.forms import BrowseSearchForm
from numpy import vectorize

def source_list(request):
    """
    Page with a list of the user's Sources.
    Redirect to the About page if the user isn't logged in or doesn't have any Sources.
    """

    if request.user.is_authenticated():
        your_sources = Source.get_sources_of_user(request.user)
        your_sources_dicts = [dict(id=s.id,
                                   name=s.name,
                                   your_role=s.get_member_role(request.user),)
                              for s in your_sources]
        other_public_sources = Source.get_other_public_sources(request.user)

        # Here we get the map sources
        map_sources = get_map_sources()

        list_thumbnails = []
        # Here we get a list of a list of images, these will be displayed
        # within each of the description windows.
        # the latest images source will not be passed into the javascript functions
        for source in map_sources:
            list_thumbnails.append((source["latest_images"],source["id"]))
            del source["latest_images"]
        
        if your_sources:
            return render_to_response('images/source_list.html', {
                'your_sources': your_sources_dicts,
                'map_sources': map_sources,
                'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
                'other_public_sources': other_public_sources,
                'list_thumbnails': list_thumbnails,
                },
                context_instance=RequestContext(request)
            )

    # not used
    return HttpResponseRedirect(reverse('source_about'))

# This isn't really used anymore, since we now display the Home page when
# the user is logged out.
def source_about(request):
    """
    Page that explains what Sources are and how to use them.
    """

    if request.user.is_authenticated():
        if Source.get_sources_of_user(request.user):
            user_status = 'has_sources'
        else:
            user_status = 'no_sources'
    else:
        user_status = 'anonymous'

    return render_to_response('images/source_about.html', {
        'user_status': user_status,
        'public_sources': Source.get_public_sources(),
        },
        context_instance=RequestContext(request)
    )


@login_required
def source_new(request):
    """
    Page with the form to create a new Source.
    """

    # We can get here one of two ways: either we just got to the form
    # page, or we just submitted the form.  If POST, we submitted; if
    # GET, we just got here.
    if request.method == 'POST':
        # Bind the forms to the submitted POST data.
        sourceForm = ImageSourceForm(request.POST)
        location_key_form = LocationKeyForm(request.POST)
        pointGenForm = PointGenForm(request.POST)
        annotationAreaForm = AnnotationAreaPercentsForm(request.POST)

        # <form>.is_valid() calls <form>.clean() and checks field validity.
        # Make sure is_valid() is called for all forms, so all forms are checked and
        # all relevant error messages appear.
        source_form_is_valid = sourceForm.is_valid()
        location_key_form_is_valid = location_key_form.is_valid()
        point_gen_form_is_valid = pointGenForm.is_valid()
        annotation_area_form_is_valid = annotationAreaForm.is_valid()

        if source_form_is_valid and location_key_form_is_valid \
           and point_gen_form_is_valid and annotation_area_form_is_valid:

            # Since sourceForm is a ModelForm, after calling sourceForm's
            # is_valid(), a Source instance is created.  We retrieve this
            # instance and add the other values to it before saving to the DB.
            newSource = sourceForm.instance

            for key_field in ['key1', 'key2', 'key3', 'key4', 'key5']:
                if key_field in location_key_form.cleaned_data:
                    setattr(newSource, key_field, location_key_form.cleaned_data[key_field])

            newSource.default_point_generation_method = PointGen.args_to_db_format(**pointGenForm.cleaned_data)
            newSource.image_annotation_area = AnnotationAreaUtils.percentages_to_db_format(**annotationAreaForm.cleaned_data)
            newSource.labelset = LabelSet.getEmptyLabelset()
            newSource.save()

            # Make the current user an admin of the new source
            newSource.assign_role(request.user, Source.PermTypes.ADMIN.code)

            # Add a success message
            messages.success(request, 'Source successfully created.')
            
            # Redirect to the source's main page
            return HttpResponseRedirect(reverse('source_main', args=[newSource.id]))
        else:
            # Show the form again, with error message
            messages.error(request, 'Please correct the errors below.')
    else:
        # Unbound (empty) forms
        sourceForm = ImageSourceForm()
        location_key_form = LocationKeyForm()
        pointGenForm = PointGenForm()
        annotationAreaForm = AnnotationAreaPercentsForm()

    # RequestContext is needed for CSRF verification of the POST form,
    # and to correctly get the path of the CSS file being used.
    return render_to_response('images/source_new.html', {
        'sourceForm': sourceForm,
        'location_key_form': location_key_form,
        'pointGenForm': pointGenForm,
        'annotationAreaForm': annotationAreaForm,
        },
        context_instance=RequestContext(request)
    )




@source_visibility_required('source_id')
def source_main(request, source_id):
    """
    Main page for a particular source.
    """

    source = get_object_or_404(Source, id=source_id)

    members = source.get_members_ordered_by_role()
    memberDicts = [dict(username=member.username,
                        role=source.get_member_role(member))
                   for member in members]

    all_images = source.get_all_images()
    latest_images = all_images.order_by('-upload_date')[:3]
    browse_url_base = reverse('visualize_source', args=[source.id])

    image_stats = dict(
        total = all_images.count(),
        total_link = browse_url_base,
        annotated = all_images.filter(status__annotatedByHuman=True).count(),
    )
    if source.enable_robot_classifier:
        image_stats.update( dict(
            annotated_link = browse_url_base + '?image_status=' + BrowseSearchForm.STATUS_CONFIRMED,
            not_annotated = all_images.filter(status__annotatedByHuman=False, status__annotatedByRobot=False).count(),
            not_annotated_link = browse_url_base + '?image_status=' + BrowseSearchForm.STATUS_NEEDS_ANNOTATION,
            not_human_annotated = all_images.filter(status__annotatedByHuman=False, status__annotatedByRobot=True).count(),
            not_human_annotated_link = browse_url_base + '?image_status=' + BrowseSearchForm.STATUS_UNCONFIRMED,
        ))
    else:
        image_stats.update( dict(
            annotated_link = browse_url_base + '?image_status=' + BrowseSearchForm.STATUS_ANNOTATED,
            not_annotated = all_images.filter(status__annotatedByHuman=False).count(),
            not_annotated_link = browse_url_base + '?image_status=' + BrowseSearchForm.STATUS_NEEDS_ANNOTATION,
        ))

    ### PREPARE ALL ROBOT STATS ###
    robot_stats = make_robot_stats(source_id, 3)
    source.latitude = source.latitude[:8]
    source.longitude = source.longitude[:8]

    return render_to_response('images/source_main.html', {
        'source': source,
        'loc_keys': ', '.join(source.get_key_list()),
        'members': memberDicts,
        'latest_images': latest_images,
        'image_stats': image_stats,
        'robot_stats':robot_stats,
        },
        context_instance=RequestContext(request)
)

@source_permission_required('source_id', perm=Source.PermTypes.ADMIN.code)
def source_edit(request, source_id):
    """
    Edit a source: name, visibility, location keys, etc.
    """

    source = get_object_or_404(Source, id=source_id)

    if request.method == 'POST':

        # Cancel
        cancel = request.POST.get('cancel', None)
        if cancel:
            messages.success(request, 'Edit cancelled.')
            return HttpResponseRedirect(reverse('source_main', args=[source_id]))

        # Submit
        sourceForm = ImageSourceForm(request.POST, instance=source)
        location_key_edit_form = LocationKeyEditForm(request.POST, source_id=source_id)
        pointGenForm = PointGenForm(request.POST)
        annotationAreaForm = AnnotationAreaPercentsForm(request.POST)

        # Make sure is_valid() is called for all forms, so all forms are checked and
        # all relevant error messages appear.
        source_form_is_valid = sourceForm.is_valid()
        location_key_edit_form_is_valid = location_key_edit_form.is_valid()
        point_gen_form_is_valid = pointGenForm.is_valid()
        annotation_area_form_is_valid = annotationAreaForm.is_valid()

        if source_form_is_valid and location_key_edit_form_is_valid \
           and point_gen_form_is_valid and annotation_area_form_is_valid:

            editedSource = sourceForm.instance

            for key_field in ['key1', 'key2', 'key3', 'key4', 'key5']:
                if key_field in location_key_edit_form.cleaned_data:
                    setattr(editedSource, key_field, location_key_edit_form.cleaned_data[key_field])

            editedSource.default_point_generation_method = PointGen.args_to_db_format(**pointGenForm.cleaned_data)
            editedSource.image_annotation_area = AnnotationAreaUtils.percentages_to_db_format(**annotationAreaForm.cleaned_data)
            editedSource.save()

            messages.success(request, 'Source successfully edited.')
            return HttpResponseRedirect(reverse('source_main', args=[source_id]))

        else:

            messages.error(request, 'Please correct the errors below.')
    else:
        # Just reached this form page
        sourceForm = ImageSourceForm(instance=source)
        location_key_edit_form = LocationKeyEditForm(source_id=source_id)
        pointGenForm = PointGenForm(source=source)
        annotationAreaForm = AnnotationAreaPercentsForm(source=source)

    return render_to_response('images/source_edit.html', {
        'source': source,
        'editSourceForm': sourceForm,
        'location_key_edit_form': location_key_edit_form,
        'pointGenForm': pointGenForm,
        'annotationAreaForm': annotationAreaForm,
        },
        context_instance=RequestContext(request)
    )


# helper function to format numpy outputs
def myfmt(r):
    return "%.0f" % (r,)

#
# This functions prepares the confusion matrix for download in a csv file. input namestr determines whether it's the full of functional confusion matrix. INPUT source_id is included for permission reasons only.
#
@source_visibility_required('source_id')
def cm_download(request, source_id, robot_version, namestr):
    vecfmt = vectorize(myfmt)
    (fullcm, labelIds) = get_confusion_matrix(Robot.objects.get(version = robot_version))
    if namestr == "full":
        cm = fullcm
        labelObjects = Label.objects.filter()
    else:
        (cm, placeholder, labelIds) = collapse_confusion_matrix(fullcm, labelIds)
        labelObjects = LabelGroup.objects.filter()

    #creating csv file
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment;filename=confusion_matrix.csv'
    writer = csv.writer(response)
    
    ngroups = len(labelIds)
    for i in range(ngroups):
        row = []
        row.append(labelObjects.get(id=labelIds[i]).name)
        row.extend(vecfmt(cm[i, :]))
        writer.writerow(row)

    return response


"""
This file exports the alleviate curve file
"""
@source_visibility_required('source_id')
def alleviate_download(request, source_id, robot_version):
    alleviate_meta = get_alleviate_meta(Robot.objects.get(version = robot_version))
    with open(alleviate_meta['plot_path'], 'r') as png:
        response = HttpResponse(png.read(), mimetype='application/png')
        response['Content-Disposition'] = 'inline;filename=alleviate' + str(robot_version) + '.png'
        return response
    pdf.closed


@source_permission_required('source_id', perm=Source.PermTypes.ADMIN.code)
def source_admin(request, source_id):
    """
    Either invites a user to the source or changes their permission in the source.
    """

    source = get_object_or_404(Source, id=source_id)

    if request.method == 'POST':

        inviteForm = SourceInviteForm(request.POST, source_id=source_id)
        changePermissionForm = SourceChangePermissionForm(request.POST, source_id=source_id, user=request.user)
        removeUserForm = SourceRemoveUserForm(request.POST, source_id=source_id, user=request.user)
        sendInvite = request.POST.get('sendInvite', None)
        changePermission = request.POST.get('changePermission', None)
        removeUser = request.POST.get('removeUser', None)
        deleteSource = request.POST.get('Delete', None)

        if inviteForm.is_valid() and sendInvite:

            invite = SourceInvite(
                sender=request.user,
                recipient=User.objects.get(username=inviteForm.cleaned_data['recipient']),
                source=source,
                source_perm=inviteForm.cleaned_data['source_perm'],
            )
            invite.save()

            messages.success(request, 'Your invite has been sent!')
            return HttpResponseRedirect(reverse('source_main', args=[source_id]))
        elif changePermissionForm.is_valid() and changePermission:

            source.reassign_role(
                user=User.objects.get(id=changePermissionForm.cleaned_data['user']),
                role=changePermissionForm.cleaned_data['perm_change']
            )

            messages.success(request, 'Permission for user has changed.')
            return HttpResponseRedirect(reverse('source_main', args=[source_id]))
        elif removeUserForm.is_valid() and removeUser:
            source.remove_role(User.objects.get(id=removeUserForm.cleaned_data['user']))

            messages.success(request, 'User has been removed from the source.')
            return HttpResponseRedirect(reverse('source_main', args=[source_id]))
        elif deleteSource:
            images = source.get_all_images()
            annotations = Annotation.objects.filter(source = source_id).all()
            annotations.delete()
            
            for img in images:
              original = img.original_file
              original.delete_thumbnails()
              original.delete()
            images.delete()

            source.delete()
            messages.success(request, 'Source has been Deleted.')
            
            return HttpResponseRedirect('/')
          
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Just reached this form page
        inviteForm = SourceInviteForm(source_id=source_id)
        changePermissionForm = SourceChangePermissionForm(source_id=source_id, user=request.user)
        removeUserForm = SourceRemoveUserForm(source_id=source_id, user=request.user)

    return render_to_response('images/source_invite.html', {
        'source': source,
        'inviteForm': inviteForm,
        'changePermissionForm': changePermissionForm,
        'removeUserForm': removeUserForm
        },
        context_instance=RequestContext(request)
        )


@login_required
def invites_manage(request):
    """
    Manage sent and received invites.
    """

    if request.method == 'POST':

        if ('accept' in request.POST) or ('decline' in request.POST):
            sender_id = request.POST['sender']
            source_id = request.POST['source']

            try:
                invite = SourceInvite.objects.get(sender__id=sender_id, recipient=request.user, source__id=source_id)
            except SourceInvite.DoesNotExist:
                messages.error(request, "Sorry, there was an error with this invite.\n"
                                        "Maybe the user who sent it withdrew the invite, or you already accepted or declined earlier.")
            else:
                if 'accept' in request.POST:
                    source = Source.objects.get(id=source_id)
                    source.assign_role(invite.recipient, invite.source_perm)

                    invite.delete()
                    messages.success(request, 'Invite accepted!')
                    return HttpResponseRedirect(reverse('source_main', args=[source.id]))
                elif 'decline' in request.POST:
                    invite.delete()
                    messages.success(request, 'Invite declined.')

        elif 'delete' in request.POST:
            recipient_id = request.POST['recipient']
            source_id = request.POST['source']

            try:
                invite = SourceInvite.objects.get(recipient__id=recipient_id, sender=request.user, source__id=source_id)
            except SourceInvite.DoesNotExist:
                messages.error(request, "Sorry, there was an error with this invite.\n"
                                        "Maybe you already deleted it earlier, or the user who received it already accepted or declined.")
            else:
                invite.delete()
                messages.success(request, 'Invite deleted.')

    return render_to_response('images/invites_manage.html', {
        'invitesSent': request.user.invites_sent.all(),
        'invitesReceived': request.user.invites_received.all(),
        },
        context_instance=RequestContext(request)
        )


@image_visibility_required('image_id')
def image_detail(request, image_id):
    """
    View for seeing an image's full size and details/metadata.
    """

    image = get_object_or_404(Image, id=image_id)
    source = image.source
    metadata = image.metadata

    # Get the metadata fields (including the right no. of keys for the source)
    # and organize into fieldsets.  The image detail form already has this
    # logic, so let's just borrow the form's functionality...
    imageDetailForm = ImageDetailForm(source=source, initial=model_to_dict(metadata))
    fieldsets = imageDetailForm.fieldsets

    # ...But we don't need the form's "Other" value fields.
    # (Code note: [:] creates a copy of the list, so we're not iterating over the same list we're removing things from)
    for field in fieldsets['keys'][:]:
        if field.name.endswith('_other'):
            fieldsets['keys'].remove(field)

    detailsets = dict()
    for key, fieldset in fieldsets.items():
        detailsets[key] = [dict(label=field.label,
                                name=field.name,
                                value=getattr(metadata, field.name))
                         for field in fieldset]

    # Feel free to change this constant according to the page layout.
    MAX_SCALED_WIDTH = 800
    if image.original_width > MAX_SCALED_WIDTH:
        # Parameters into the easy_thumbnails template tag:
        # (specific width, height that keeps the aspect ratio)
        thumbnail_dimensions = (MAX_SCALED_WIDTH, 0)
    else:
        # No thumbnail needed
        thumbnail_dimensions = False

    # Next and previous image links
    next_image = get_next_image(image)
    prev_image = get_prev_image(image)

    # Annotation status
    if image.status.annotatedByHuman:
        annotation_status = "Complete"
    elif image_has_any_human_annotations(image):
        annotation_status = "Partially annotated"
    else:
        annotation_status = "Not started"

    # Should we include a link to the annotation area edit page?
    annotation_area_editable = image_annotation_area_is_editable(image)

    return render_to_response('images/image_detail.html', {
        'source': source,
        'image': image,
        'next_image': next_image,
        'prev_image': prev_image,
        'metadata': metadata,
        'detailsets': detailsets,
        'has_thumbnail': bool(thumbnail_dimensions),
        'thumbnail_dimensions': thumbnail_dimensions,
        'annotation_status': annotation_status,
        'annotation_area_editable': annotation_area_editable,
        },
        context_instance=RequestContext(request)
    )

@image_permission_required('image_id', perm=Source.PermTypes.EDIT.code)
def image_detail_edit(request, image_id):
    """
    Edit image details.
    """

    image = get_object_or_404(Image, id=image_id)
    source = image.source
    metadata = image.metadata

    old_height_in_cm = metadata.height_in_cm

    if request.method == 'POST':

        # Cancel
        cancel = request.POST.get('cancel', None)
        if cancel:
            messages.success(request, 'Edit cancelled.')
            return HttpResponseRedirect(reverse('image_detail', args=[image.id]))

        # Submit
        imageDetailForm = ImageDetailForm(request.POST, instance=metadata, source=source)

        if imageDetailForm.is_valid():
            editedMetadata = imageDetailForm.instance
            editedMetadata.save()

            if editedMetadata.height_in_cm != old_height_in_cm:
                image.after_height_cm_change()

            messages.success(request, 'Image successfully edited.')
            return HttpResponseRedirect(reverse('image_detail', args=[image.id]))
        else:
            transaction.rollback()  # Don't save "Other" location values to database
            messages.error(request, 'Please correct the errors below.')
    else:
        # Just reached this form page
        imageDetailForm = ImageDetailForm(instance=metadata, source=source)

    return render_to_response('images/image_detail_edit.html', {
        'source': source,
        'image': image,
        'imageDetailForm': imageDetailForm,
        },
        context_instance=RequestContext(request)
        )


def import_groups(request, fileLocation):
    """
    Create label groups through a text file.
    NOTE: This method might be obsolete.
    """
    file = open(fileLocation, 'r') #opens the file for reading
    for line in file:
        line = line.replace("; ", ';')
        words = line.split(';')

        #creates a label object and stores it in the database
        group = LabelGroup(name=words[0], code=words[1])
        group.save()
    file.close()
    

@source_permission_required('source_id', perm=Source.PermTypes.ADMIN.code)
def import_labels(request, source_id):
    """
    Create a labelset through a text file.
    NOTE: This view might be obsolete.  Or site-admin only.
    """

    source = get_object_or_404(Source, id=source_id)

    #creates a new labelset for the source
    labelset = LabelSet()
    labelset.save()

    labelsImported = 0
    newLabels = 0
    existingLabels = 0

    if request.method == 'POST':
        labelImportForm = LabelImportForm(request.POST, request.FILES)

        if labelImportForm.is_valid():

            file = request.FILES['labels_file']

            # We'll assume we're using an InMemoryUploadedFile, as opposed to a filename of a temp-disk-storage file.
            # If we encounter a case where we have a filename, use the below:
            #file = open(fileLocation, 'r') #opens the file for reading

            #iterates over each line in the file and processes it
            for line in file:
                #sanitizes and splits apart the string/line
                line = line.strip().replace("; ", ';')
                words = line.split(';')

                # Ignore blank lines
                if line == '':
                    continue

                labelName, labelCode, groupName = words[0], words[1], words[2]
                group = get_object_or_404(LabelGroup, name=groupName)

                # (1) Create a new label, (2) use an existing label,
                # or (3) throw an error if a file label and existing
                # label of the same code don't match.
                try:
                    existingLabel = Label.objects.get(code=labelCode)
                except Label.DoesNotExist:
                    #creates a label object and stores it in the database
                    label = Label(name=labelName, code=labelCode, group=group)
                    label.save()
                    newLabels += 1
                else:
                    if (existingLabel.name == labelName and
                        existingLabel.code == labelCode and
                        existingLabel.group == group
                    ):
                        label = existingLabel
                        existingLabels += 1
                    else:
                        raise ValidationError(
                            """Our database already has a label with code %s,
                            but it doesn't match yours.
                            Ours: %s, %s, %s
                            Yours: %s, %s, %s""" % (
                            labelCode,
                            existingLabel.name, existingLabel.code, existingLabel.group.name,
                            labelName, labelCode, groupName
                            ))

                #adds label to the labelset
                labelset.labels.add(label)
                labelsImported += 1

            file.close() #closes file since we're done

            labelset.description = labelImportForm.cleaned_data['labelset_description']
            labelset.save()
            source.labelset = labelset
            source.save()

            success_msg = "%d labels imported: %d new labels and %d existing labels." % (labelsImported, newLabels, existingLabels)
            messages.success(request, success_msg)
            return HttpResponseRedirect(reverse('source_main', args=[source_id]))

        else:
            messages.error(request, 'Please correct the errors below.')

    # GET
    else:
        labelImportForm = LabelImportForm()

    return render_to_response('images/label_import.html', {
            'labelImportForm': labelImportForm,
            'source': source,
            },
            context_instance=RequestContext(request)
    )

@source_visibility_required('source_id')
def robot_stats_all(request, source_id):

    robot_stats = make_robot_stats(source_id, 0)
    source = Source.objects.get(id = source_id)

    return render_to_response('images/robot_stats_all.html', {
        'robot_stats':robot_stats,
        'source':source,
        },
        context_instance=RequestContext(request)
)


def make_robot_stats(source_id, nbr_robots):

    ### PREPARE ALL ROBOT STATS ###
    source = Source.objects.get(id = source_id)
    groupObjects = LabelGroup.objects.filter()
    labelObjects = Label.objects.filter()
    validRobots = source.get_valid_robots()

    if nbr_robots > 0:
        validRobots = validRobots[-nbr_robots:]
    
    robotlist = []
    for robot in validRobots:
        (fullcm, labelIds) = get_confusion_matrix(robot)
        (fullcm_n, row_sums) = confusion_matrix_normalize(fullcm)
        cm_str = format_cm_for_display(fullcm_n, row_sums, labelObjects, labelIds)
        fullacc = accuracy_from_cm(fullcm)

        (funccm, placeholder, groupIds) = collapse_confusion_matrix(fullcm, labelIds)
        (funccm_n, row_sums) = confusion_matrix_normalize(funccm)
        cm_func_str = format_cm_for_display(funccm_n, row_sums, groupObjects, groupIds)
        funcacc = accuracy_from_cm(funccm)

        cmlist = []
        cmlist.append(dict(        
            cm_str = cm_str,
            ncols = len(labelIds) + 2,
            ndiags = len(labelIds) + 3,
            idstr = 'dialog' + str(robot.version) + 'full',
            namestr = 'full',
            acc = '%.1f' % (100*fullacc[0]),
            kappa = '%.1f' % (100*fullacc[1]),
        ))
        cmlist.append(dict(        
            cm_str = cm_func_str,
            ncols = len(groupIds) + 2,
            ndiags = len(groupIds) + 3,
            idstr = 'dialog' + str(robot.version) + 'func',
            namestr = 'func',
            acc = '%.1f' % (100*funcacc[0]),
            kappa = '%.1f' % (100*funcacc[1]),
        ))

        f = open(robot.path_to_model + '.meta.json')
        jsonstring = f.read()
        f.close()
        meta = json.loads(jsonstring)

        robotlist.append(dict(
            cmlist = cmlist,
            alleviate_meta = get_alleviate_meta(robot),
            version = robot.version,
            nsamples = sum(meta['final']['trainData']['labelhist']['org']),
            train_time = str(int(round(meta['totalRuntime']))),
            date = '%s' %  datetime.datetime.fromtimestamp(os.path.getctime(robot.path_to_model + '.meta.json')).date()
        ))
    
    if not validRobots:
        robot_stats = dict(
            robotlist = robotlist,
            has_robot=False,
        )
    else:
        robot_stats = dict(
            robotlist = robotlist,
            has_robot=True,
            most_recent_run_date = '%s' %  time.ctime(os.path.getmtime(validRobots[-1].path_to_model + '.meta.json')),
        )

    return robot_stats

