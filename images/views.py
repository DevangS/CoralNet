import datetime

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
from annotations.forms import AnnotationAreaPercentsForm
from annotations.model_utils import AnnotationAreaUtils
from annotations.models import LabelGroup, Label, Annotation, LabelSet
from CoralNet.decorators import labelset_required, permission_required, visibility_required
from CoralNet.exceptions import FileContentError
from annotations.utils import image_annotation_area_is_editable

from images.models import Source, Image, Metadata, Point, SourceInvite, ImageStatus
from images.forms import ImageSourceForm, ImageUploadOptionsForm, ImageDetailForm, AnnotationImportForm, ImageUploadForm, LabelImportForm, PointGenForm, SourceInviteForm
from images.model_utils import PointGen
from images.utils import filename_to_metadata, find_dupe_image, get_location_value_objs, generate_points
import json

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


@visibility_required('source_id')
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

    stats = dict(
        num_images=all_images.count(),
        need_comp_anno_images=all_images.filter(status__annotatedByHuman=False, status__annotatedByRobot=False).count(),
        need_human_anno_images=all_images.filter(status__annotatedByHuman=False, status__annotatedByRobot=True).count(),
        anno_completed_images=all_images.filter(status__annotatedByHuman=True).count(),
        num_annotations=Annotation.objects.filter(image__source=source).count(),
    )
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
        'stats': stats,
		'robotStats':robotStats,
        },
        context_instance=RequestContext(request)
        )


# Must have admin permission for the Source whose id is source_id
@permission_required(Source.PermTypes.ADMIN.code, (Source, 'id', 'source_id'))
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


@permission_required(Source.PermTypes.ADMIN.code, (Source, 'id', 'source_id'))
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


@visibility_required('source_id')
def image_detail(request, image_id, source_id):
    """
    View for seeing an image's full size and details/metadata.
    """

    image = get_object_or_404(Image, id=image_id)
    source = get_object_or_404(Source, id=source_id)
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

    # Default max viewing width
    # Feel free to change the constant according to the page layout.
    scaled_width = min(image.original_width, 800)

    # Next and previous image links
    next_image = image.get_next()
    prev_image = image.get_previous()

    # Should we include a link to the annotation area edit page?
    annotation_area_editable = image_annotation_area_is_editable(image_id)

    return render_to_response('images/image_detail.html', {
        'source': source,
        'image': image,
        'next_image': next_image,
        'prev_image': prev_image,
        'metadata': metadata,
        'detailsets': detailsets,
        'scaled_width': scaled_width,
        'annotation_area_editable': annotation_area_editable,
        },
        context_instance=RequestContext(request)
    )

@permission_required(Source.PermTypes.EDIT.code, (Source, 'id', 'source_id'))
def image_detail_edit(request, image_id, source_id):
    """
    Edit image details.
    """

    image = get_object_or_404(Image, id=image_id)
    source = get_object_or_404(Source, id=source_id)
    metadata = image.metadata

    old_height_in_cm = metadata.height_in_cm

    if request.method == 'POST':

        # Cancel
        cancel = request.POST.get('cancel', None)
        if cancel:
            messages.success(request, 'Edit cancelled.')
            return HttpResponseRedirect(reverse('image_detail', args=[source_id, image_id]))

        # Submit
        imageDetailForm = ImageDetailForm(request.POST, instance=metadata, source=source)

        if imageDetailForm.is_valid():
            editedMetadata = imageDetailForm.instance
            editedMetadata.save()

            if editedMetadata.height_in_cm != old_height_in_cm:
                image.after_height_cm_change()

            messages.success(request, 'Image successfully edited.')
            return HttpResponseRedirect(reverse('image_detail', args=[source_id, image_id]))
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


@permission_required(Source.PermTypes.ADMIN.code, (Source, 'id', 'source_id'))
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
    

@permission_required(Source.PermTypes.ADMIN.code, (Source, 'id', 'source_id'))
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

def annotations_file_to_python(annoFile, source):
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
    parseErrorMsgBase = 'On line %d:\n%s\n%s'
    
    numOfKeys = source.num_of_keys()
    uniqueLabelCodes = []

    # The order of the words/tokens is encoded here.  If the order ever
    # changes, we should only have to change this part.
    wordsFormat = ['value'+str(i) for i in range(1, numOfKeys+1)]
    wordsFormat += ['date', 'row', 'col', 'label']
    numOfWordsExpected = len(wordsFormat)

    annotationsDict = dict()

    for lineNum, line in enumerate(annoFile, 1):

        # Sanitize the line and split it into words/tokens.
        # Allow for separators of ";" or "; "
        cleanedLine = line.strip().replace("; ", ';')
        words = cleanedLine.split(';')

        # Check that all words/tokens are there.
        if len(words) != numOfWordsExpected:
            raise FileContentError(parseErrorMsgBase % (lineNum, line, "We expected %d pieces of data, but only found %d." % (numOfWordsExpected, len(words)) ))

        # Encode the line data into a dictionary: {'value1':'Shore2', 'row':'575', ...}
        lineData = dict(zip(wordsFormat, words))

        
        # Check that the label code corresponds to a label in the database
        # and in the source's labelset.
        # Only check this if the label code hasn't been seen before
        # in the annotations file.
        labelCode = lineData['label']
        if labelCode not in uniqueLabelCodes:

            labelObjs = Label.objects.filter(code=labelCode)
            if len(labelObjs) == 0:
                raise FileContentError(parseErrorMsgBase % (lineNum, line, "This line has label code %s, but our database has no label with this code." % labelCode))

            labelObj = labelObjs[0]
            if labelObj not in source.labelset.labels.all():
                raise FileContentError(parseErrorMsgBase % (lineNum, line, "This line has label code %s, but your labelset has no label with this code." % labelCode))

            uniqueLabelCodes.append(labelCode)

        # Get and check the photo year to make sure it's valid.
        # We'll assume the year is the first 4 characters of the date.
        year = lineData['date'][:4]
        try:
            datetime.date(int(year),1,1)
        # Year is non-coercable to int, or year is out of range (e.g. 0 or negative)
        except ValueError:
            raise FileContentError(parseErrorMsgBase % (lineNum, line, "%s is not a valid year." % year))

        # TODO: Check if the row and col in this line are a valid row and col
        # for the image.  Need the image to do that, though...


        # Use the location values and the year to build a string identifier for the image, such as:
        # Shore1;Reef5;...;2008
        valueList = [lineData['value'+str(i)] for i in range(1,numOfKeys+1)]
        imageIdentifier = get_image_identifier(valueList, year)

        # Add/update a dictionary entry for the image with this identifier.
        # The dict entry's value is a list of labels.  Each label is a dict:
        # {'row':'484', 'col':'320', 'label':'POR'}
        if not annotationsDict.has_key(imageIdentifier):
            annotationsDict[imageIdentifier] = []
            
        annotationsDict[imageIdentifier].append(
            dict(row=lineData['row'], col=lineData['col'], label=lineData['label'])
        )

    annoFile.close()

    return annotationsDict


def image_upload_process(imageFiles, optionsForm, source, currentUser, annoFile):
    """
    Helper method for the image upload view and the image+annotation
    import view.
    """

    uploadedImages = []
    duplicates = 0
    imagesUploaded = 0
    annotationsImported = 0

    dupeOption = optionsForm.cleaned_data['skip_or_replace_duplicates']
    importedUser = get_imported_user()

    annotationData = None
    if annoFile:
        try:
            annotationData = annotations_file_to_python(annoFile, source)
        except FileContentError as errorDetail:
            return dict(error=True,
                message='Error reading labels file %s. %s' % (annoFile.name, errorDetail),
            )

    for imageFile in imageFiles:

        filename = imageFile.name
        metadataDict = None
        metadata = Metadata(height_in_cm=source.image_height_in_cm)

        if optionsForm.cleaned_data['specify_metadata'] == 'filenames':

            try:
                metadataDict = filename_to_metadata(filename, source)

            # Filename parse error.
            # TODO: check for validity of the file type and contents, too.
            except (ValueError, StopIteration):
                return dict(error=True,
                    message='Upload failed - Error when parsing the filename %s for metadata.' % filename,
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

            status = ImageStatus(hasRandomPoints=True, annotatedByHuman=True)
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

                label = Label.objects.filter(code=anno['label'])[0]

                # Save the Annotation in the database, marking the annotations as imported.
                annotation = Annotation(user=importedUser,
                                        point=point, image=img, label=label, source=source)
                annotation.save()

                annotationsImported += 1
                pointNum += 1

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
    if duplicates > 0:
        if dupeOption == 'replace':
            duplicateMsg = "%d duplicate images replaced." % duplicates
        else:
            duplicateMsg = "%d duplicate images skipped." % duplicates
    else:
        duplicateMsg = ''

    if annotationsImported > 0:
        annotationMsg = "%d annotations imported." % annotationsImported
    else:
        annotationMsg = ''

    uploadedMsg = "%d images uploaded." % imagesUploaded
    successMsg = uploadedMsg + ' ' + duplicateMsg + ' ' + annotationMsg

    return dict(error=False,
        uploadedImages=uploadedImages,
        message=successMsg,
    )


@permission_required(Source.PermTypes.EDIT.code, (Source, 'id', 'source_id'))
def image_upload(request, source_id):
    """
    View for uploading images to a source.
    Should be improved later to have AJAX uploading.
    """

    source = get_object_or_404(Source, id=source_id)
    uploadedImages = []

    if request.method == 'POST':
        imageForm = ImageUploadForm(request.POST, request.FILES)
        optionsForm = ImageUploadOptionsForm(request.POST, source=source)

        # Need getlist instead of simply request.FILES, in order to handle
        # multiple files.
        imageFiles = request.FILES.getlist('files')

        # TODO: imageForm.is_valid() just validates the first image file.
        # Make sure all image files are checked to be valid images.
        if imageForm.is_valid() and optionsForm.is_valid():

            resultDict = image_upload_process(imageFiles=imageFiles,
                                              optionsForm=optionsForm,
                                              source=source,
                                              currentUser=request.user,
                                              annoFile=None)

            if resultDict['error']:
                messages.error(request, resultDict['message'])
                transaction.rollback()
            else:
                uploadedImages = resultDict['uploadedImages']
                messages.success(request, resultDict['message'])

        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        imageForm = ImageUploadForm()
        optionsForm = ImageUploadOptionsForm(source=source)

    return render_to_response('images/image_upload.html', {
        'source': source,
        'imageForm': imageForm,
        'optionsForm': optionsForm,
        'uploadedImages': uploadedImages,
        },
        context_instance=RequestContext(request)
    )


@permission_required(Source.PermTypes.EDIT.code, (Source, 'id', 'source_id'))
@labelset_required('source_id', 'You need to create a labelset for your source before you can import annotations.')
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
        optionsForm = ImageUploadOptionsForm(request.POST, source=source)

        # Need getlist instead of simply request.FILES, in order to handle
        # multiple files.
        imageFiles = request.FILES.getlist('files')

        # TODO: imageForm.is_valid() just validates the first image file.
        # Make sure all image files are checked to be valid images.
        if annotationForm.is_valid() and imageForm.is_valid() and optionsForm.is_valid():

            annoFile = request.FILES['annotations_file']

            resultDict = image_upload_process(imageFiles=imageFiles,
                                              optionsForm=optionsForm,
                                              source=source,
                                              currentUser=request.user,
                                              annoFile=annoFile)

            if resultDict['error']:
                messages.error(request, resultDict['message'])
                transaction.rollback()
                revision_context_manager.invalidate()

#            # This also works, although the try and with make it harder to read, IMO
#            try:
#                with reversion.revision:
#                    resultDict = image_upload_process(imageFiles=imageFiles,
#                            optionsForm=optionsForm,
#                            source=source,
#                            currentUser=request.user,
#                            annoFile=annoFile)
#
#                    if resultDict['error']:
#                        raise ValueError()
#            except ValueError:
#                messages.error(request, resultDict['message'])
#                transaction.rollback()

            else:
                uploadedImages = resultDict['uploadedImages']
                messages.success(request, resultDict['message'])

        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        annotationForm = AnnotationImportForm()
        imageForm = ImageUploadForm()
        optionsForm = ImageUploadOptionsForm(source=source)

    return render_to_response('images/image_and_annotation_upload.html', {
        'source': source,
        'annotationForm': annotationForm,
        'imageForm': imageForm,
        'optionsForm': optionsForm,
        'uploadedImages': uploadedImages,
        },
        context_instance=RequestContext(request)
    )
