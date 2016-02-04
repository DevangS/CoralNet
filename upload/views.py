from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.contrib import messages
from annotations.model_utils import AnnotationAreaUtils
from decorators import source_permission_required
from images.model_utils import PointGen
from images.models import Source
from lib.exceptions import FileContentError
from lib.utils import JsonResponse
from .forms import MultiImageUploadForm, ImageUploadForm, ImageUploadOptionsForm, AnnotationImportForm, AnnotationImportOptionsForm, CSVImportForm, MetadataImportForm, ImportArchivedAnnotationsForm
from .utils import annotations_file_to_python, image_upload_process, metadata_dict_to_dupe_comparison_key, check_image_filename, store_csv_file, load_archived_csv, check_archived_csv, import_archived_annotations
from visualization.forms import ImageSpecifyForm

import csv

@source_permission_required('source_id', perm=Source.PermTypes.EDIT.code)
def image_upload(request, source_id):
    """
    This view serves the image upload page.  It doesn't actually do any
    upload processing, though; that's left to the Ajax views.
    """

    source = get_object_or_404(Source, id=source_id)

    images_form = MultiImageUploadForm()
    options_form = ImageUploadOptionsForm(source=source)
    csv_import_form = CSVImportForm()
    annotation_import_form = AnnotationImportForm()
    annotation_import_options_form = AnnotationImportOptionsForm(source=source)
    proceed_to_manage_metadata_form = ImageSpecifyForm(
        initial=dict(specify_method='image_ids'),
        source=source,
    )

    auto_generate_points_message = (
        "We will generate points for the images you upload.\n"
        "Your Source's point generation settings: {pointgen}\n"
        "Your Source's annotation area settings: {annoarea}").format(
            pointgen=PointGen.db_to_readable_format(source.default_point_generation_method),
            annoarea=AnnotationAreaUtils.db_format_to_display(source.image_annotation_area,
        ),
    )

    return render_to_response('upload/image_upload.html', {
        'source': source,
        'images_form': images_form,
        'options_form': options_form,
        'csv_import_form': csv_import_form,
        'annotation_import_form': annotation_import_form,
        'annotation_import_options_form': annotation_import_options_form,
        'proceed_to_manage_metadata_form': proceed_to_manage_metadata_form,
        'auto_generate_points_message': auto_generate_points_message,
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
        metadataOption = request.POST['metadataOption']

        # List of filename statuses.
        statusList = []

        for index, filename in enumerate(filenames):

            if metadataOption == 'filenames':
                result = check_image_filename(filename, source)
            else:
                result = check_image_filename(filename, source, verify_metadata=False)

            status = result['status']
            metadata_key = None

            if 'metadata_dict' in result:
                # We successfully extracted metadata from the filename.
                metadata_key = metadata_dict_to_dupe_comparison_key(result['metadata_dict'])

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
            elif status == 'possible_dupe':
                dupe_image = result['dupe']
                statusList.append(dict(
                    status=status,
                    metadataKey=metadata_key,
                    url=reverse('image_detail', args=[dupe_image.id]),
                    title=dupe_image.get_image_element_title(),
                ))

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
    Takes an annotation .txt file and processes it.  Saves the processing
    results to a "shelved" dictionary file on disk, ready to be used in
    subsequent image-upload operations.  Returns status info in a JSON
    response.
    """

    source = get_object_or_404(Source, id=source_id)

    if request.method == 'POST':

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


@source_permission_required('source_id', perm=Source.PermTypes.EDIT.code)
def image_upload_ajax(request, source_id):
    """
    After the "Start upload" button is clicked, this view is entered once
    for each image file.  This view saves the image and its
    points/annotations to the database.
    """

    source = get_object_or_404(Source, id=source_id)

    # Retrieve image related fields
    image_form = ImageUploadForm(request.POST, request.FILES)
    options_form = ImageUploadOptionsForm(request.POST, source=source)

    annotation_dict_id = request.POST.get('annotation_dict_id', None)
    annotation_options_form = AnnotationImportOptionsForm(request.POST, source=source)

    csv_dict_id = request.POST.get('csv_dict_id', None)

    # Check for validity of the file (filetype and non-corruptness) and
    # the options forms.
    if image_form.is_valid():
        if options_form.is_valid():
            if annotation_options_form.is_valid():
                resultDict = image_upload_process(
                    imageFile=image_form.cleaned_data['file'],
                    imageOptionsForm=options_form,
                    annotation_dict_id=annotation_dict_id,
                    annotation_options_form=annotation_options_form,
                    csv_dict_id=csv_dict_id,
                    metadata_import_form_class=MetadataImportForm,
                    source=source,
                    currentUser=request.user,
                )
                return JsonResponse(resultDict)
            else:
                return JsonResponse(dict(
                    status='error',
                    message="Annotation options were invalid",
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

@source_permission_required('source_id', perm=Source.PermTypes.EDIT.code)
def csv_file_process_ajax(request,source_id):

    source = get_object_or_404(Source, id=source_id)

    if request.method == 'POST':

        csv_import_form = CSVImportForm(request.POST, request.FILES)

        if not csv_import_form.is_valid():
            return JsonResponse(dict(
                status='error',
                message=csv_import_form.errors['csv_file'][0],
            ))

        csv_file = csv_import_form.cleaned_data['csv_file']

        try:
            csv_dict, csv_dict_id = store_csv_file(csv_file, source)
        except FileContentError as error:
            return JsonResponse(dict(
                status='error',
                message=error.message,
             ))

        # Check if all the CSV metadata is valid.
        for filename, data in csv_dict.iteritems():
            metadata_import_form = MetadataImportForm(
                source.id, False, data
            )
            if not metadata_import_form.is_valid():
                # One of the filenames' metadata is not valid. Get one
                # error message and return that.
                for field_name, messages in metadata_import_form.errors.iteritems():
                    field_label = metadata_import_form.fields[field_name].label
                    if messages != []:
                        error_message = messages[0]
                        return JsonResponse(dict(
                            status='error',
                            message="({filename} - {field_label}) {message}".format(
                                filename=filename,
                                field_label=field_label,
                                message=error_message,
                            )
                        ))

        return JsonResponse(dict(
            status='ok',
            csv_dict_id=csv_dict_id,
            csv_dict=csv_dict,
        ))

    return JsonResponse(dict(
        status='error',
        message="Request was not POST",
    ))

@source_permission_required('source_id', perm=Source.PermTypes.EDIT.code)
def upload_archived_annotations(request, source_id):

    source = get_object_or_404(Source, id=source_id)

    # First of all, we will check if the source contains any duplicate images file names. If so, warn them.
    if source.all_image_names_are_unique():
        non_unique = []
    else:
        non_unique = source.get_all_images().filter(metadata__name__in = source.get_nonunique_image_names())

    # Now check the form.
    if request.method == 'POST':
        csv_import_form = ImportArchivedAnnotationsForm(request.POST, request.FILES) # grab the form

        if csv_import_form.is_valid():
            file_ = csv_import_form.cleaned_data['csv_file'] # grab the file handle
            
            # These next four lines look very strange. But for some reason, I had to explicitly assign it to True for the logic
            # to work in subsequent python code. Must be some miscommunication btw. django forms and python.
            if csv_import_form.cleaned_data['is_uploading_annotations_not_just_points'] == True:
                uploading_anns_and_points = True
            else:
                uploading_anns_and_points = False
            
            try:
                anndict = load_archived_csv(source_id, file_) # load CSV file.
            except Exception as me:
                messages.error(request, 'Error parsing input file. Error message: {}.'.format(me))
                return HttpResponseRedirect(reverse('annotation_upload', args=[source_id]))

            # all is OK, store in session.
            request.session['archived_annotations'] = anndict 
            request.session['uploading_anns_and_points'] = uploading_anns_and_points
            # add a message to the user.
            if uploading_anns_and_points:
                messages.success(request, 'You are about to upload point locations AND labels.')
            else:
                messages.success(request, 'You are about to upload point locations only.')
            return HttpResponseRedirect(reverse('annotation_upload_verify', args=[source_id]))
        else:
            messages.error(request, 'File does not seem to be a csv file')
            return HttpResponseRedirect(reverse('annotation_upload', args=[source_id]))

    else:
        form = ImportArchivedAnnotationsForm()
    
    return render_to_response('upload/upload_archived_annotations.html', {'form': form, 'source': source, 'non_unique': non_unique}, context_instance=RequestContext(request))


@source_permission_required('source_id', perm=Source.PermTypes.EDIT.code)
def verify_archived_annotations(request, source_id):
    source = get_object_or_404(Source, id=source_id)
    if request.method == 'POST': #there is only the 'submit' button, so no need to check what submit.
        import_archived_annotations(source_id, request.session['archived_annotations'], with_labels = request.session['uploading_anns_and_points']) # do the actual import.
        messages.success(request, 'Successfully imported annotations.')
        return HttpResponseRedirect(reverse('source_main', args=[source.id]))
    else:
        if 'archived_annotations' in request.session.keys():
            status = check_archived_csv(source_id, request.session['archived_annotations'], with_labels = request.session['uploading_anns_and_points'])
        else:
            messages.error(request, 'Session timeout. Try again or contact system admin.') # This is a very odd situation, since we just added the data to the session.
            return HttpResponseRedirect(reverse('source_main', args=[source.id]))

        return render_to_response('upload/verify_archived_annotations.html', {'status': status, 'source': source}, context_instance=RequestContext(request))


