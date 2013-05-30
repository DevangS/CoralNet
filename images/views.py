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
from images.forms import *
from images.model_utils import PointGen
from images.utils import *
from lib.utils import get_map_sources
import json , csv, os.path, time
from numpy import array

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

    image_stats = dict(
        total = all_images.count(),
        anno_completed = all_images.filter(status__annotatedByHuman=True).count(),
    )
    if source.enable_robot_classifier:
        image_stats.update( dict(
            need_comp_anno = all_images.filter(status__annotatedByHuman=False, status__annotatedByRobot=False).count(),
            need_human_anno = all_images.filter(status__annotatedByHuman=False, status__annotatedByRobot=True).count(),
            need_human_anno_first = get_first_image(source, dict(status__annotatedByHuman=False, status__annotatedByRobot=True)),
        ))
    else:
        image_stats.update( dict(
            need_anno = all_images.filter(status__annotatedByHuman=False).count(),
            need_anno_first = get_first_image(source, dict(status__annotatedByHuman=False)),
        ))


    latestRobot = source.get_latest_robot()
    if latestRobot == None:
        robotStats = dict(
            hasRobot=False,
        )
    else:
        f = open(latestRobot.path_to_model + '.meta.json')
        jsonstring = f.read()
        f.close()
        meta=json.loads(jsonstring)
        
        lastedit = 'Last Robot Run: %s' %  time.ctime(os.path.getmtime(\
        latestRobot.path_to_model + '.meta.json'))

        #getting raw confusion matrix from json file
        if 'cmOpt' in meta['hp']['gridStats']:
            cmx = meta['hp']['gridStats']['cmOpt']
        else:
            cmx = meta['hp']['gridStats'][-1]['cmOpt']
          
        labelMap = meta['labelMap']
        
        dimension = len(labelMap)
        matrixSize =  dimension + 1
        sizeOfNewMatrix = (int( len(cmx) + matrixSize) )
        newcm = [None] * (sizeOfNewMatrix -1 )

        temp = []
        groupCM = []

        #create an array out of the the raw cm list
        for x in range(len(cmx)):
            temp.append(cmx[x])
            if (x+1) % dimension == 0:
                groupCM.append(temp)
                temp = []
        groupCM = array(groupCM)
        
        
        
        labelNames = []
        groupsNames = []
        label_fullName = []

        #getting label objects 
        for ids in labelMap:
          labelNames.append( get_object_or_404(Label, id=ids))
        for label in labelNames:
          groupsNames.append(str(label.group.name))
        for label in labelNames:
          label_fullName.append(str(label.name))


        numofGroups = len( set(groupsNames) )
        setMap = list(set(groupsNames) )
        groupLen = len(setMap)

        sizeOfGroup = len(setMap) ** 2
        groupCols = []
        temp = None

        #reduce the cols and create a list of cols
        for col in range(groupLen):
            for x in range(dimension):
                if setMap[col] == groupsNames[x]:
                    if temp == None:
                        temp = groupCM[:,x]
                    else:
                        temp += groupCM[:,x]
            groupCols.append(temp)
            temp = None
 
        temp = []
        colList = []
        for x in groupCols:
            colList.append ( x.tolist())

        #convert to single matrix format from cols list
        cmint = []
        for x in range(dimension):
            for col in range(len(colList)):
                temp.append( colList[col][x])
            cmint.append(temp)
            temp = []

        #reduce rows and create a list of rows
        cmint = array(cmint)
        temp = None
        cmout = []
        for row in range(groupLen):
            for x in range(dimension):
                if setMap[row] == groupsNames[x]:
                    if temp == None:
                        temp = cmint[x,:]
                    else:
                        temp += cmint[x,:]
            cmout.append(temp)
            temp = None

        rowList = []
        for x in cmout:
            rowList.append ( x.tolist())

        rowSum = 0
        rowSumList = []
        #convert to single matrix format from row list
        finalGroup = []
        for x in rowList:
            for cell in x:
                rowSum += cell
            rowSumList.append(rowSum)
            rowSum = 0

        i = 0
        #convert to single matrix format from row list
        finalGroup = []
        for x in rowList:
            for cell in x:
                if rowSumList[i] == 0:
                    percent = 0.0
                else:
                    percent = cell/float(rowSumList[i])
                finalGroup.append(("%.2f" % percent).lstrip('0'))
            i += 1     
             
        i = j = 0
        groupcm = [None] * (len(finalGroup) + groupLen )

        #functional group CM
        for items in finalGroup:
            if ( i % (groupLen + 1 ) ) == 0:
                groupcm[i] = setMap[j]
                j+=1
                i+=1
            groupcm[i] = items
            i+=1
        
        i = j = 0
        fullcm = [None] * (matrixSize + len(cmx) -1)
       

        full_row_sum = []
        temp = 0
        

        #full cm
        for items in cmx:
            temp += items
            i += 1
            if(i % (matrixSize-1)) == 0:
                full_row_sum.append(temp)
                temp = 0
            
        i = 0
        for x in cmx:
            if(i % matrixSize) == 0:
               fullcm[i] = label_fullName[j]
               j += 1
               i += 1
            
            if full_row_sum[j-1] == 0:
                percent = 0.0
            else:
                percent = x/float(full_row_sum[j-1])
            fullcm[i] = (("%.2f" % percent).lstrip('0'))
            i += 1     
             

        robotStats = dict(
            version=latestRobot.version,
            edit = lastedit,
            trainTime=round(meta['totalRuntime']),
            precision = 100 * (1 - meta['hp']['estPrecision']),
            fullcm = fullcm,
            labels = label_fullName,
            cm = groupcm,
            labelMap = setMap,
            row_sum = rowSumList,
            full_row_sum = full_row_sum,
            matrixSize = len(setMap) + 1,
            FullmatrixSize = matrixSize,
            full_diaglen = matrixSize + 1,
            diaglen = len(setMap) + 2,
            hasRobot=True,
        )


    return render_to_response('images/source_main.html', {
        'source': source,
        'loc_keys': ', '.join(source.get_key_list()),
        'members': memberDicts,
        'latest_images': latest_images,
        'image_stats': image_stats,
		    'robotStats':robotStats,
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

@source_visibility_required('source_id')
def csv_download(request, source_id):
    source = get_object_or_404(Source, id=source_id)
    latestRobot = source.get_latest_robot()
    
    if latestRobot == None:
        return HttpResponse('No Robot Stats')  
    else:
        f = open(latestRobot.path_to_model + '.meta.json')
        jsonstring = f.read()
        f.close()
        meta=json.loads(jsonstring)

        #getting raw confusion matrix from json file
        if 'cmOpt' in meta['hp']['gridStats']:
            cmx = meta['hp']['gridStats']['cmOpt']
        else:
            cmx = meta['hp']['gridStats'][-1]['cmOpt']
        labelMap = meta['labelMap']
        dimension = len(labelMap)

        temp = []
        groupCM = []

        #create an array out of the the raw cm list
        for x in range(len(cmx)):
            temp.append(cmx[x])
            if (x+1) % dimension == 0:
                groupCM.append(temp)
                temp = []
        groupCM = array(groupCM)
              
        
        labelNames = []
        label_fullName = []

        #getting label objects 
        for ids in labelMap:
          labelNames.append( get_object_or_404(Label, id=ids))
        for label in labelNames:
          label_fullName.append(str(label.name))
        
        #creating csv file
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment;filename=Full_CM.csv'
        writer = csv.writer(response)

        writer.writerow(label_fullName)
        for rows in groupCM:
          writer.writerow (rows.tolist())

        return response


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


