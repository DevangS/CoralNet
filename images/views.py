from collections import defaultdict
import datetime
import os
import shelve
from django.conf import settings

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms import ValidationError
from django.forms.models import model_to_dict
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.template import RequestContext
from reversion.revisions import revision_context_manager

from userena.models import User
from accounts.utils import get_imported_user
from annotations.forms import AnnotationAreaPercentsForm, AnnotationImportForm, AnnotationImportOptionsForm
from annotations.model_utils import AnnotationAreaUtils
from annotations.models import LabelGroup, Label, Annotation, LabelSet
from lib.exceptions import *
from annotations.utils import image_annotation_area_is_editable, image_has_any_human_annotations
from decorators import source_permission_required, image_visibility_required, image_permission_required, source_labelset_required, source_visibility_required

from images.models import Source, Image, Metadata, Point, SourceInvite, ImageStatus
from images.forms import *
from images.model_utils import PointGen
from images.utils import *
import json
from lib.utils import JsonResponse
from CoralNet.utils import rand_string

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
        
        if your_sources:
            return render_to_response('images/source_list.html', {
                'your_sources': your_sources_dicts,
                'other_public_sources': other_public_sources,
                },
                context_instance=RequestContext(request)
            )

    return HttpResponseRedirect(reverse('source_about'))

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
        # A form bound to the POST data
        sourceForm = ImageSourceForm(request.POST)
        pointGenForm = PointGenForm(request.POST)
        annotationAreaForm = AnnotationAreaPercentsForm(request.POST)

        # is_valid() calls our ModelForm's clean() and checks validity
        source_form_is_valid = sourceForm.is_valid()
        point_gen_form_is_valid = pointGenForm.is_valid()
        annotation_area_form_is_valid = annotationAreaForm.is_valid()

        if source_form_is_valid and point_gen_form_is_valid and annotation_area_form_is_valid:
            # After calling a ModelForm's is_valid(), an instance is created.
            # We can get this instance and add a bit more to it before saving to the DB.
            newSource = sourceForm.instance
            newSource.default_point_generation_method = PointGen.args_to_db_format(**pointGenForm.cleaned_data)
            newSource.image_annotation_area = AnnotationAreaUtils.percentages_to_db_format(**annotationAreaForm.cleaned_data)
            newSource.labelset = LabelSet.getEmptyLabelset()
            newSource.save()

            # Make the user a source admin
            newSource.assign_role(request.user, Source.PermTypes.ADMIN.code)

            # Add a success message
            messages.success(request, 'Source successfully created.')
            
            # Redirect to the source's main page
            return HttpResponseRedirect(reverse('source_main', args=[newSource.id]))
        else:
            # Show the form again, with error message
            messages.error(request, 'Please correct the errors below.')
    else:
        # An unbound form (empty form)
        sourceForm = ImageSourceForm()
        pointGenForm = PointGenForm()
        annotationAreaForm = AnnotationAreaPercentsForm()

    # RequestContext needed for CSRF verification of POST form,
    # and to correctly get the path of the CSS file being used.
    return render_to_response('images/source_new.html', {
        'sourceForm': sourceForm,
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
    latest_images = all_images.order_by('-upload_date')[:5]

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
        robotStats = dict(
            version=latestRobot.version,
            trainTime=round(meta['totalRuntime']),
            precision = 100 * (1 - meta['hp']['estPrecision']),
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
        pointGenForm = PointGenForm(request.POST)
        annotationAreaForm = AnnotationAreaPercentsForm(request.POST)

        # Make sure is_valid() is called for all forms, so all forms are checked and
        # all relevant error messages appear.
        source_form_is_valid = sourceForm.is_valid()
        point_gen_form_is_valid = pointGenForm.is_valid()
        annotation_area_form_is_valid = annotationAreaForm.is_valid()

        if source_form_is_valid and point_gen_form_is_valid and annotation_area_form_is_valid:
            editedSource = sourceForm.instance
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
        pointGenForm = PointGenForm(source=source)
        annotationAreaForm = AnnotationAreaPercentsForm(source=source)

    return render_to_response('images/source_edit.html', {
        'source': source,
        'editSourceForm': sourceForm,
        'pointGenForm': pointGenForm,
        'annotationAreaForm': annotationAreaForm,
        },
        context_instance=RequestContext(request)
        )


@source_permission_required('source_id', perm=Source.PermTypes.ADMIN.code)
def source_invite(request, source_id):
    """
    Invite a user to this Source.
    """

    source = get_object_or_404(Source, id=source_id)

    if request.method == 'POST':

        inviteForm = SourceInviteForm(request.POST, source_id=source_id)

        if inviteForm.is_valid():

            invite = SourceInvite(
                sender=request.user,
                recipient=User.objects.get(username=inviteForm.cleaned_data['recipient']),
                source=source,
                source_perm=inviteForm.cleaned_data['source_perm'],
            )
            invite.save()

            messages.success(request, 'Your invite has been sent!')
            return HttpResponseRedirect(reverse('source_main', args=[source_id]))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Just reached this form page
        inviteForm = SourceInviteForm(source_id=source_id)

    return render_to_response('images/source_invite.html', {
        'source': source,
        'inviteForm': inviteForm,
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


def get_image_identifier(valueList, year):
    """
    Use the location values and the year to build a string identifier for an image:
    Shore1;Reef5;...;2008
    """
    return ';'.join(valueList + [year])

def annotations_file_to_python(annoFile, source, expecting_labels):
    """
    Takes: an annotations file

    Returns: the Pythonized annotations:
    A dictionary like this:
    {'Shore1;Reef3;...;2008': [{'row':'695', 'col':'802', 'label':'POR'},
                               {'row':'284', 'col':'1002', 'label':'ALG'},
                               ...],
     'Shore2;Reef5;...;2009': [...]
     ... }

    Checks for: correctness of file formatting, i.e. all words/tokens are there on each line
    (will throw an error otherwise)
    """

    # We'll assume annoFile is an InMemoryUploadedFile, as opposed to a filename of a temp-disk-storage file.
    # If we encounter a case where we have a filename, use the below:
    #annoFile = open(annoFile, 'r')

    # Format args: line number, line contents, error message
    file_error_format_str = str_consts.ANNOTATION_CHECK_FULL_ERROR_MESSAGE_FMTSTR
    
    numOfKeys = source.num_of_keys()
    uniqueLabelCodes = []

    # The order of the words/tokens is encoded here.  If the order ever
    # changes, we should only have to change this part.
    words_format_without_label = ['value'+str(i) for i in range(1, numOfKeys+1)]
    words_format_without_label += ['date', 'row', 'col']
    words_format_with_label = words_format_without_label + ['label']

    num_words_with_label = len(words_format_with_label)
    num_words_without_label = len(words_format_without_label)

    # The annotation dict needs to be kept on disk temporarily until all the
    # Ajax upload requests are done. Thus, we'll use Python's shelve module
    # to make a persistent dict.
    if not os.access(settings.SHELVED_ANNOTATIONS_DIR, os.R_OK | os.W_OK):
        # Don't catch this error and display it to the user.
        # Just let it become a server error to be e-mailed to the admins.
        raise DirectoryAccessError(
            "The SHELVED_ANNOTATIONS_DIR either does not exist, is not readable, or is not writable. Please rectify this."
        )
    annotation_dict_id = rand_string(10)
    annotation_dict = shelve.open(os.path.join(
        settings.SHELVED_ANNOTATIONS_DIR,
        'source{source_id}_{dict_id}'.format(
            source_id=source.id,
            dict_id=annotation_dict_id,
        ),
    ))

    for line_num, line in enumerate(annoFile, 1):

        stripped_line = line.strip()

        # Ignore empty lines.
        if stripped_line == '':
            continue

        # Split the line into words/tokens.
        unstripped_words = stripped_line.split(';')
        # Strip leading and trailing whitespace from each token.
        words = [w.strip() for w in unstripped_words]

        # Check that all expected words/tokens are there.
        is_valid_format_with_label = (len(words) == num_words_with_label)
        is_valid_format_without_label = (len(words) == num_words_without_label)
        words_format_is_valid = (
            (expecting_labels and is_valid_format_with_label)
            or (not expecting_labels and (is_valid_format_with_label or is_valid_format_without_label))
        )
        if expecting_labels:
            num_words_expected = num_words_with_label
        else:
            num_words_expected = num_words_without_label

        if not words_format_is_valid:
            annotation_dict.close()
            annoFile.close()
            raise FileContentError(file_error_format_str.format(
                line_num=line_num,
                line=stripped_line,
                error=str_consts.ANNOTATION_CHECK_TOKEN_COUNT_ERROR_FMTSTR.format(
                    num_words_expected=num_words_expected,
                    num_words_found=len(words),
                )
            ))

        # Encode the line data into a dictionary: {'value1':'Shore2', 'row':'575', ...}
        if is_valid_format_with_label:
            lineData = dict(zip(words_format_with_label, words))
        else:  # valid format without label
            lineData = dict(zip(words_format_without_label, words))

        if expecting_labels:
            # Check that the label code corresponds to a label in the database
            # and in the source's labelset.
            # Only check this if the label code hasn't been seen before
            # in the annotations file.

            label_code = lineData['label']
            if label_code not in uniqueLabelCodes:

                labelObjs = Label.objects.filter(code=label_code)
                if len(labelObjs) == 0:
                    annotation_dict.close()
                    annoFile.close()
                    raise FileContentError(file_error_format_str.format(
                        line_num=line_num,
                        line=stripped_line,
                        error=str_consts.ANNOTATION_CHECK_LABEL_NOT_IN_DATABASE_ERROR_FMTSTR.format(label_code=label_code),
                    ))

                labelObj = labelObjs[0]
                if labelObj not in source.labelset.labels.all():
                    annotation_dict.close()
                    annoFile.close()
                    raise FileContentError(file_error_format_str.format(
                        line_num=line_num,
                        line=stripped_line,
                        error=str_consts.ANNOTATION_CHECK_LABEL_NOT_IN_LABELSET_ERROR_FMTSTR.format(label_code=label_code),
                    ))

                uniqueLabelCodes.append(label_code)

        # Get and check the photo year to make sure it's valid.
        # We'll assume the year is the first 4 characters of the date.
        year = lineData['date'][:4]
        try:
            datetime.date(int(year),1,1)
        # Year is non-coercable to int, or year is out of range (e.g. 0 or negative)
        except ValueError:
            annotation_dict.close()
            annoFile.close()
            raise FileContentError(file_error_format_str.format(
                line_num=line_num,
                line=stripped_line,
                error=str_consts.ANNOTATION_CHECK_YEAR_ERROR_FMTSTR.format(year=year),
            ))

        # TODO: Check if the row and col in this line are a valid row and col
        # for the image.  Need the image to do that, though...


        # Use the location values and the year to build a string identifier for the image, such as:
        # Shore1;Reef5;...;2008
        valueList = [lineData['value'+str(i)] for i in range(1,numOfKeys+1)]
        imageIdentifier = get_image_identifier(valueList, year)

        # Add/update a dictionary entry for the image with this identifier.
        # The dict entry's value is a list of labels.  Each label is a dict:
        # {'row':'484', 'col':'320', 'label':'POR'}
        if not annotation_dict.has_key(imageIdentifier):
            annotation_dict[imageIdentifier] = []

        # Append the annotation as a dict containing row, col, and label
        # (or just row and col, if no labels).
        #
        # Can't append directly to annotation_dict[imageIdentifier], due to
        # how shelved dicts work. So we use this pattern with a temporary
        # variable.
        # See http://docs.python.org/library/shelve.html?highlight=shelve#example
        tmp_data = annotation_dict[imageIdentifier]
        if expecting_labels:
            tmp_data.append(
                dict(row=lineData['row'], col=lineData['col'], label=lineData['label'])
            )
        else:
            tmp_data.append(
                dict(row=lineData['row'], col=lineData['col'])
            )
        annotation_dict[imageIdentifier] = tmp_data

    annoFile.close()

    return (annotation_dict, annotation_dict_id)


def multi_image_upload_process(imageFiles, imageOptionsForm, annotationOptionsForm, source, currentUser, annoFile):
    """
    Helper method for the image upload view and the image+annotation
    import view.
    """

    uploadedImages = []
    duplicates = 0
    imagesUploaded = 0
    annotationsImported = 0
    importedUser = get_imported_user()

    dupeOption = imageOptionsForm.cleaned_data['skip_or_replace_duplicates']

    annotationData = None
    if annoFile:
        try:
            annotationData = annotations_file_to_python(annoFile, source)
        except FileContentError as error:
            return dict(error=True,
                message="Error reading labels file {filename} - {error}.".format(filename=annoFile.name, error=error.message),
            )

    for imageFile in imageFiles:

        filename = imageFile.name
        metadataDict = None
        metadata = Metadata(height_in_cm=source.image_height_in_cm)

        if imageOptionsForm.cleaned_data['specify_metadata'] == 'filenames':

            try:
                metadataDict = filename_to_metadata(filename, source)
            except FilenameError as error:
                # Filename parse error.
                return dict(error=True,
                    message="Upload failed on {filename} - {error}.".format(filename=filename, error=error.message),
                )

            # Detect duplicate images and handle them
            dupe = find_dupe_image(source, **metadataDict)
            if dupe:
                duplicates += 1
                if dupeOption == 'skip':
                    # Skip uploading this file.
                    continue
                elif dupeOption == 'replace':
                    # Proceed uploading this file, and delete the dupe.
                    dupe.delete()

            # Set the metadata
            valueDict = get_location_value_objs(source, metadataDict['values'], createNewValues=True)
            photoDate = datetime.date(year = int(metadataDict['year']),
                             month = int(metadataDict['month']),
                             day = int(metadataDict['day']))

            metadata.name = metadataDict['name']
            metadata.photo_date = photoDate
            for key, value in valueDict.iteritems():
                setattr(metadata, key, value)

        else:
            metadata.name = filename

        # Image + annotation import form
        # Assumes we got the images' metadata (from filenames or otherwise)
        if annotationData:

            pointsOnlyOption = annotationOptionsForm.cleaned_data['points_only']

            # Use the location values and the year to build a string identifier for the image, such as:
            # Shore1;Reef5;...;2008
            imageIdentifier = get_image_identifier(metadataDict['values'], metadataDict['year'])

            # Use the identifier as the index into the annotation file's data.
            if not annotationData.has_key(imageIdentifier):
                return dict(error=True,
                    message='%s seems to have no annotations for the image file %s, which has the following keys:\n%s' % (
                        annoFile.name, imageFile.name, imageIdentifier.replace(';',' '))
                )

            imageAnnotations = annotationData[imageIdentifier]

            status = ImageStatus()
            status.save()

            metadata.annotation_area = AnnotationAreaUtils.IMPORTED_STR
            metadata.save()

            img = Image(original_file=imageFile,
                    uploaded_by=currentUser,
                    point_generation_method=PointGen.args_to_db_format(
                        point_generation_type=PointGen.Types.IMPORTED,
                        imported_number_of_points=len(imageAnnotations)
                    ),
                    metadata=metadata,
                    source=source,
                    status=status,
                  )
            img.save()

            # Iterate over this image's annotations and save them.
            pointNum = 1
            for anno in imageAnnotations:

                # Save the Point in the database.
                point = Point(row=anno['row'], column=anno['col'], point_number=pointNum, image=img)
                point.save()

                if not pointsOnlyOption:
                    label = Label.objects.filter(code=anno['label'])[0]

                    # Save the Annotation in the database, marking the annotations as imported.
                    annotation = Annotation(user=importedUser,
                                            point=point, image=img, label=label, source=source)
                    annotation.save()

                    annotationsImported += 1

                pointNum += 1

            img.status.hasRandomPoints = True
            if not pointsOnlyOption:
                img.status.annotatedByHuman = True
            img.status.save()

        # Image upload form, no annotations
        else:
            status = ImageStatus()
            status.save()

            metadata.annotation_area = source.image_annotation_area
            metadata.save()

            # Save the image into the DB
            img = Image(original_file=imageFile,
                    uploaded_by=currentUser,
                    point_generation_method=source.default_point_generation_method,
                    metadata=metadata,
                    source=source,
                    status=status,
                  )
            img.save()

            # Generate and save points
            generate_points(img)

        # Up to 5 uploaded images will be shown
        # upon successful upload.
        # Prepend to list, so most recent image comes first
        uploadedImages.insert(0, img)
        if len(uploadedImages) > 5:
            uploadedImages = uploadedImages[:5]

        imagesUploaded += 1

    # Construct success message.
    success_message = image_upload_success_message(
        num_images_uploaded=imagesUploaded,
        num_dupes=duplicates,
        dupe_option=dupeOption,
        num_annotations=annotationsImported,
    )

    return dict(error=False,
        uploadedImages=uploadedImages,
        message=success_message,
    )


def image_upload_process(imageFile, imageOptionsForm,
                         is_uploading_points_or_annotations,
                         annotation_dict_id,
                         annotation_options_form,
                         source, currentUser):

    dupeOption = imageOptionsForm.cleaned_data['skip_or_replace_duplicates']

    filename = imageFile.name
    is_dupe = False
    metadata_dict = None
    metadata_obj = Metadata(height_in_cm=source.image_height_in_cm)

    if imageOptionsForm.cleaned_data['specify_metadata'] == 'filenames':

        filename_check_result = check_image_filename(filename, source)
        filename_status = filename_check_result['status']

        if filename_status == 'error':
            # This case should never happen if the pre-upload
            # status checking is doing its job, but just in case...
            return dict(
                status=filename_status,
                message=u"{m}".format(m=filename_check_result['message']),
                link=None,
                title=None,
            )

        elif filename_status == 'dupe':
            is_dupe = True
            dupe_image = filename_check_result['dupe']

            if dupeOption == 'skip':
                # This case should never happen if the pre-upload
                # status checking is doing its job, but just in case...
                return dict(
                    status='error',
                    message="Skipped (duplicate found)",
                    link=reverse('image_detail', args=[dupe_image.id]),
                    title=dupe_image.get_image_element_title(),
                )
            elif dupeOption == 'replace':
                # Delete the dupe, and proceed with uploading this file.
                dupe_image.delete()

        # Set the metadata
        metadata_dict = filename_check_result['metadata_dict']

        value_dict = get_location_value_objs(source, metadata_dict['values'], createNewValues=True)
        photo_date = datetime.date(
            year = int(metadata_dict['year']),
            month = int(metadata_dict['month']),
            day = int(metadata_dict['day'])
        )

        metadata_obj.name = metadata_dict['name']
        metadata_obj.photo_date = photo_date
        for key, value in value_dict.iteritems():
            setattr(metadata_obj, key, value)
    else:
        # Not specifying data from filenames.
        # *** Unused case for now ***
        metadata_obj.name = filename
        is_dupe = False

    # Use the location values and the year to build a string identifier for the image, such as:
    # Shore1;Reef5;...;2008
    # Convert to a string (instead of a unicode string) for the shelve key lookup.
    image_identifier = str(get_image_identifier(metadata_dict['values'], metadata_dict['year']))

    image_annotations = None
    has_points_or_annotations = False
    if is_uploading_points_or_annotations:
        annotation_dict = shelve.open(os.path.join(
            settings.SHELVED_ANNOTATIONS_DIR,
            'source{source_id}_{dict_id}'.format(
                source_id=source.id,
                dict_id=annotation_dict_id,
            ),
        ))
        if annotation_dict.has_key(image_identifier):
            image_annotations = annotation_dict[image_identifier]
            has_points_or_annotations = True
        annotation_dict.close()

    if has_points_or_annotations:
        # Image upload with points/annotations

        is_uploading_annotations_not_just_points = annotation_options_form.cleaned_data['is_uploading_annotations_not_just_points']
        imported_user = get_imported_user()

        status = ImageStatus()
        status.save()

        metadata_obj.annotation_area = AnnotationAreaUtils.IMPORTED_STR
        metadata_obj.save()

        img = Image(
            original_file=imageFile,
            uploaded_by=currentUser,
            point_generation_method=PointGen.args_to_db_format(
                point_generation_type=PointGen.Types.IMPORTED,
                imported_number_of_points=len(image_annotations)
            ),
            metadata=metadata_obj,
            source=source,
            status=status,
        )
        img.save()

        # Iterate over this image's annotations and save them.
        point_num = 0
        for anno in image_annotations:

            # Save the Point in the database.
            point_num += 1
            point = Point(row=anno['row'], column=anno['col'], point_number=point_num, image=img)
            point.save()

            if is_uploading_annotations_not_just_points:
                label = Label.objects.filter(code=anno['label'])[0]

                # Save the Annotation in the database, marking the annotations as imported.
                annotation = Annotation(user=imported_user,
                    point=point, image=img, label=label, source=source)
                annotation.save()

        img.status.hasRandomPoints = True
        if is_uploading_annotations_not_just_points:
            img.status.annotatedByHuman = True
        img.status.save()
    else:
        # Image upload, no points/annotations
        image_status = ImageStatus()
        image_status.save()

        metadata_obj.annotation_area = source.image_annotation_area
        metadata_obj.save()

        # Save the image into the DB
        img = Image(original_file=imageFile,
            uploaded_by=currentUser,
            point_generation_method=source.default_point_generation_method,
            metadata=metadata_obj,
            source=source,
            status=image_status,
        )
        img.save()

        # Generate and save points
        generate_points(img)

    if is_dupe:
        success_message = "Uploaded (replaced duplicate)"
    else:
        success_message = "Uploaded"

    return dict(
        status='ok',
        message=success_message,
        link=reverse('image_detail', args=[img.id]),
        title=img.get_image_element_title(),
        image_id=img.id,
    )


@source_permission_required('source_id', perm=Source.PermTypes.EDIT.code)
def image_upload(request, source_id):
    """
    View for uploading images to a source.
    """

    source = get_object_or_404(Source, id=source_id)
    uploaded_images = []

    images_form = MultiImageUploadForm()
    options_form = ImageUploadOptionsForm(source=source)
    annotation_import_form = AnnotationImportForm()
    annotation_import_options_form = AnnotationImportOptionsForm(source=source)

    auto_generate_points_message = (
        "You haven't specified any points or annotations, so we will\n"
        "generate points for the images you upload.\n"
        "Your Source's point generation settings: {pointgen}\n"
        "Your Source's annotation area settings: {annoarea}").format(
            pointgen=PointGen.db_to_readable_format(source.default_point_generation_method),
            annoarea=AnnotationAreaUtils.db_format_to_display(source.image_annotation_area,
        ),
    )

    return render_to_response('images/image_upload.html', {
        'source': source,
        'images_form': images_form,
        'options_form': options_form,
        'annotation_import_form': annotation_import_form,
        'annotation_import_options_form': annotation_import_options_form,
        'auto_generate_points_message': auto_generate_points_message,
        'uploaded_images': uploaded_images,
        },
        context_instance=RequestContext(request)
    )


@source_permission_required('source_id', perm=Source.PermTypes.EDIT.code)
def image_upload_preview_ajax(request, source_id):
    """
    Called when a user selects files to upload in the image upload form.

    :param filenames: A list of filenames.
    :returns: A dict containing a 'statusList' specifying the status of
        each filename, or an 'error' with an error message.
    """

    source = get_object_or_404(Source, id=source_id)

    if request.method == 'POST':

        filenames = request.POST.getlist('filenames[]')

        # List of filename statuses.
        statusList = []
        # Dict that keeps track of which filenames have the same metadata
        # Each key is a set of metadata, each value is a list of file indices
        # of files with that metadata.
        # If 2 or more filenames have the same metadata, that's an error.
        metadata_match_finder = defaultdict(list)

        for index, filename in enumerate(filenames):

            result = check_image_filename(filename, source)
            status = result['status']
            metadata_key = None

            if 'metadata_dict' in result:
                # We successfully extracted metadata from the filename.
                # Add this to the metadata_match_finder.
                metadata_key = metadata_dict_to_dupe_comparison_key(result['metadata_dict'])
                if metadata_key in metadata_match_finder:
                    metadata_match_finder[metadata_key].append(index)
                else:
                    metadata_match_finder[metadata_key] = [index]

            if status == 'error':
                statusList.append(dict(
                    status=status,
                    message=u"{m}".format(m=result['message']),
                ))
            elif status == 'ok':
                statusList.append(dict(
                    status=status,
                    metadataKey=metadata_key,
                ))
            elif status == 'dupe':
                dupe_image = result['dupe']
                statusList.append(dict(
                    status=status,
                    metadataKey=metadata_key,
                    url=reverse('image_detail', args=[dupe_image.id]),
                    title=dupe_image.get_image_element_title(),
                ))

        # Check if 2 or more filenames have the same metadata (at least
        # metadata that counts for duplicate detection - location
        # values and year).
        # If so, mark all such filenames as errored.
        for metadata_key, file_index_list in metadata_match_finder.items():
            if len(file_index_list) > 1:
                for index in file_index_list:
                    statusList[index] = dict(
                        status='error',
                        message=str_consts.UPLOAD_PREVIEW_SAME_METADATA_ERROR_FMTSTR.format(
                            metadata=metadata_dupe_comparison_key_to_display(metadata_key)
                        ),
                    )

        return JsonResponse(dict(
            statusList=statusList,
        ))

    else:

        return JsonResponse(dict(
            error="Not a POST request",
        ))


@source_permission_required('source_id', perm=Source.PermTypes.EDIT.code)
def annotation_file_process_ajax(request, source_id):
    """
    Called when a user selects files to upload in the image upload form.

    Looks at the files' filenames and returns a dict containing:
    errors - List containing any errors. If there are any errors, the user
      should not be allowed to start the upload.
    warnings - List containing any warnings (i.e. things that may or may not
      actually be problems).
    """

    source = get_object_or_404(Source, id=source_id)

    if request.method == 'POST':

        #uploadable_file_names = request.POST.getlist('uploadable_file_names[]')
        #skipped_dupe_file_names = request.POST.getlist('skipped_dupe_file_names[]')

        annotation_import_form = AnnotationImportForm(request.POST, request.FILES)
        annotation_import_options_form = AnnotationImportOptionsForm(request.POST, request.FILES, source=source)

        if not annotation_import_form.is_valid():
            return JsonResponse(dict(
                status='error',
                message=annotation_import_form.errors['annotations_file'][0],
            ))

        if not annotation_import_options_form.is_valid():
            return JsonResponse(dict(
                status='error',
                message="Annotation options form is invalid",
            ))

        is_uploading_annotations_not_just_points = annotation_import_options_form.cleaned_data['is_uploading_annotations_not_just_points']
        annotations_file = annotation_import_form.cleaned_data['annotations_file']

        try:
            annotation_dict, annotation_dict_id = annotations_file_to_python(
                annotations_file, source,
                expecting_labels=is_uploading_annotations_not_just_points,
            )
        except FileContentError as error:
            return JsonResponse(dict(
                status='error',
                message=error.message,
            ))

        # Return information on how many points/annotations
        # each metadata set has in the annotation file.
        annotations_per_image = dict(
            [(k, len(v)) for k, v in annotation_dict.iteritems()]
        )
        # We're done with the shelved dict for now.
        annotation_dict.close()

        return JsonResponse(dict(
            status='ok',
            annotations_per_image=annotations_per_image,
            annotation_dict_id=annotation_dict_id,
        ))

        # The following is code that could be used to check whether each
        # selected image file has annotations in the annotation file.
#        errors = []
#        max_errors = 5
#        for filename in uploadable_file_names:
#            metadata_dict = filename_to_metadata(filename, source)
#
#            # Use the location values and the year to build a string
#            # identifier for the image, such as:
#            # Shore1;Reef5;...;2008
#            image_identifier = get_image_identifier(metadata_dict['values'], metadata_dict['year'])
#
#            # Use the identifier as the index into the annotation file's data.
#            if not annotation_data.has_key(image_identifier):
#                errors.append("The annotation file has no annotations for {filename} ({keys})".format(
#                    filename=filename,
#                    keys=image_identifier.replace(';',' '),
#                ))
#                if len(errors) >= max_errors:
#                    break
#
#        return JsonResponse(dict(
#            status='error',
#            message='\n'.join(errors),
#        ))


@source_permission_required('source_id', perm=Source.PermTypes.EDIT.code)
def image_upload_ajax(request, source_id):
    source = get_object_or_404(Source, id=source_id)

    # Retrieve image related fields
    image_form = ImageUploadForm(request.POST, request.FILES)
    options_form = ImageUploadOptionsForm(request.POST, source=source)

    # Retrieve annotation related fields
    is_uploading_points_or_annotations = request.POST.get('is_uploading_points_or_annotations', 'off')
    annotation_dict_id = request.POST.get('annotation_dict_id', None)
    annotation_options_form = AnnotationImportOptionsForm(request.POST, source=source)

    # Corner case: somehow, we're uploading with points+annotations and no
    # checked annotation file.
    if is_uploading_points_or_annotations == 'on' and annotation_dict_id is None:
        return JsonResponse(dict(
            status='error',
            message=u"{m}".format(m=str_consts.UPLOAD_ANNOTATIONS_ON_AND_NO_ANNOTATION_DICT_ERROR_STR),
            link=None,
            title=None,
        ))

    # Check for validity of the file (filetype and non-corruptness) and
    # the options forms.
    if image_form.is_valid():
        if options_form.is_valid():
            if annotation_options_form.is_valid():
                resultDict = image_upload_process(
                    imageFile=image_form.cleaned_data['file'],
                    imageOptionsForm=options_form,
                    is_uploading_points_or_annotations=is_uploading_points_or_annotations,
                    annotation_dict_id=annotation_dict_id,
                    annotation_options_form=annotation_options_form,
                    source=source,
                    currentUser=request.user,
                )
                return JsonResponse(resultDict)
            else:
                return JsonResponse(dict(
                    status='error',
                    message="Annotation options form is invalid",
                    link=None,
                    title=None,
                ))
        else:
            return JsonResponse(dict(
                status='error',
                message="Options form is invalid",
                link=None,
                title=None,
            ))
    else:
        # File error: filetype is not an image,
        # file is corrupt, file is empty, etc.
        return JsonResponse(dict(
            status='error',
            message=image_form.errors['file'][0],
            link=None,
            title=None,
        ))


@source_permission_required('source_id', perm=Source.PermTypes.ADMIN.code)
@source_labelset_required('source_id', message='You need to create a labelset for your source before you can import annotations.')
def annotation_import(request, source_id):
    """
    Upload images and import their annotations from a text file.
    Should be improved later to have AJAX uploading.
    """

    source = get_object_or_404(Source, id=source_id)

    uploadedImages = []

    if request.method == 'POST':
        annotationForm = AnnotationImportForm(request.POST, request.FILES)
        imageForm = ImageUploadForm(request.POST, request.FILES)
        imageOptionsForm = ImageUploadOptionsForm(request.POST, source=source)
        annotationOptionsForm = AnnotationImportOptionsForm(request.POST)

        # Need getlist instead of simply request.FILES, in order to handle
        # multiple files.
        imageFiles = request.FILES.getlist('files')

        # TODO: imageForm.is_valid() just validates the first image file.
        # Make sure all image files are checked to be valid images.
        if (annotationForm.is_valid() and
            imageForm.is_valid() and
            annotationOptionsForm.is_valid() and
            imageOptionsForm.is_valid() ):

            annoFile = request.FILES['annotations_file']

            resultDict = multi_image_upload_process(
                imageFiles=imageFiles,
                imageOptionsForm=imageOptionsForm,
                annotationOptionsForm=annotationOptionsForm,
                source=source,
                currentUser=request.user,
                annoFile=annoFile
            )

            if resultDict['error']:
                messages.error(request, resultDict['message'])
                transaction.rollback()
                revision_context_manager.invalidate()
            else:
                uploadedImages = resultDict['uploadedImages']
                messages.success(request, resultDict['message'])

        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        annotationForm = AnnotationImportForm()
        imageForm = ImageUploadForm()
        annotationOptionsForm = AnnotationImportOptionsForm()
        imageOptionsForm = ImageUploadOptionsForm(source=source)

    return render_to_response('images/image_and_annotation_upload.html', {
        'source': source,
        'annotationForm': annotationForm,
        'imageForm': imageForm,
        'annotationOptionsForm': annotationOptionsForm,
        'imageOptionsForm': imageOptionsForm,
        'uploadedImages': uploadedImages,
        },
        context_instance=RequestContext(request)
    )
