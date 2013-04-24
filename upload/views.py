from collections import defaultdict
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from annotations.model_utils import AnnotationAreaUtils
from decorators import source_permission_required
from images.model_utils import PointGen
from images.models import Source
from lib import str_consts
from lib.exceptions import FileContentError
from lib.utils import JsonResponse
from upload.forms import MultiImageUploadForm, ImageUploadForm, ImageUploadOptionsForm, AnnotationImportForm, AnnotationImportOptionsForm, CSVImportForm
from upload.utils import annotations_file_to_python, image_upload_process, metadata_dict_to_dupe_comparison_key, metadata_dupe_comparison_key_to_display, check_image_filename, store_csv_file, filename_to_metadata_in_csv

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
    Takes an annotation .txt file and processes it.  Saves the processing
    results to a "shelved" dictionary file on disk, ready to be used in
    subsequent image-upload operations.  Returns status info in a JSON
    response.
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
            csv_dict, csv_dict_id = store_csv_file(csv_file, source);
        except FileContentError as error:
            return JsonResponse(dict(
                status='error',
                message=error.message,
             ))

        # We're done with the shelved dict for now.
        csv_dict.close()

        return JsonResponse(dict(
            status='ok',
            csv_dict_id=csv_dict_id,
        ))

    return JsonResponse(dict(
        status='error',
        message="Request was not POST",
    ))

@source_permission_required('source_id', perm=Source.PermTypes.EDIT.code)
def image_upload_preview_with_csv_ajax(request,source_id):

    source = get_object_or_404(Source, id=source_id)

    if request.method == 'POST':

        filenames = request.POST.getlist('filenames[]')
        csv_dict_id = request.POST.get("csv_file_id");

        # List of filename statuses.
        statusList = []
        for filename in filenames:
            result = filename_to_metadata_in_csv(filename, source, csv_dict_id)
            status = result['status']

            if status == "error":
                statusList.append(dict(
                    status=status,
                    message=u"{m}".format(m=result['message']),
                ))
            else:
                #metadata_list = metadata_dict_to_list(result['metadata_dict'])
                statusList.append(dict(
                    status=status,
                    filename=filename,
                    metadata_list=result["metadata_dict"]),
                )

        return JsonResponse(dict(
            statusList=statusList,
        ))

    return JsonResponse(dict(
        status='error',
        message="Request was not POST",
    ))
