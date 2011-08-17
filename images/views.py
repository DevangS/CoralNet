from datetime import date, datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms import ValidationError
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.template import RequestContext

from guardian.decorators import permission_required
from guardian.shortcuts import assign
from accounts.models import Profile
from annotations.models import LabelGroup, Label, Annotation

from images.models import Source, Image, Metadata, Value1, Value2, Value3, Value4, Value5, Point
from images.forms import ImageSourceForm, ImageUploadForm, ImageDetailForm

from os.path import splitext


def source_list(request):
    """
    Page with a list of the user's Sources.
    Redirect to the About page if the user isn't logged in or doesn't have any Sources.
    """

    if request.user.is_authenticated():
        your_sources = Source.get_sources_of_user(request.user)
        other_sources = Source.get_other_public_sources(request.user)
        
        if your_sources:
            return render_to_response('images/source_list.html', {
                'your_sources': your_sources,
                'other_sources': other_sources,
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
    Page with the form to create a new Image Source.
    """

    # We can get here one of two ways: either we just got to the form
    # page, or we just submitted the form.  If POST, we submitted; if
    # GET, we just got here.
    if request.method == 'POST':
        # A form bound to the POST data
        form = ImageSourceForm(request.POST)

        # is_valid() calls our ModelForm's clean() and checks validity
        if form.is_valid():
            # Save the source in the database
            newSource = form.save()
            # Grant permissions for this source
            assign('source_admin', request.user, newSource)
            # Add a success message
            messages.success(request, 'Source successfully created.')
            # Redirect to the source's main page
            return HttpResponseRedirect(reverse('source_main', args=[newSource.id]))
        else:
            # Show the form again, with error message
            messages.error(request, 'Please correct the errors below.')
    else:
        # An unbound form (empty form)
        form = ImageSourceForm()

    # RequestContext needed for CSRF verification of POST form,
    # and to correctly get the path of the CSS file being used.
    return render_to_response('images/source_new.html', {
        'form': form,
        },
        context_instance=RequestContext(request)
        )

def source_main(request, source_id):
    """
    Main page for a particular image source.
    """

    source = get_object_or_404(Source, id=source_id)

    # Is there a way to make the perm check in a permission_required decorator?
    # Having to manually code the redirect to login is slightly annoying.
    if source.visible_to_user(request.user):
        members = source.get_members()
        latest_images = source.get_all_images().order_by('-upload_date')[:5]

        return render_to_response('images/source_main.html', {
            'source': source,
            'members': members,
            'latest_images': latest_images,
            },
            context_instance=RequestContext(request)
            )
    else:
        return HttpResponseRedirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

# Must have the 'source_admin' permission for the Source whose id is source_id
@permission_required('source_admin', (Source, 'id', 'source_id'))
def source_edit(request, source_id):
    """
    Edit an image source: name, visibility, location keys, etc.
    """

    source = get_object_or_404(Source, id=source_id)

    if request.method == 'POST':

        # Cancel
        cancel = request.POST.get('cancel', None)
        if cancel:
            messages.success(request, 'Edit cancelled.')
            return HttpResponseRedirect(reverse('source_main', args=[source_id]))

        # Submit
        form = ImageSourceForm(request.POST, instance=source)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Source successfully edited.')
            return HttpResponseRedirect(reverse('source_main', args=[source_id]))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Just reached this form page
        form = ImageSourceForm(instance=source)

    return render_to_response('images/source_edit.html', {
        'source': source,
        'editSourceForm': form,
        },
        context_instance=RequestContext(request)
        )


@transaction.commit_on_success    # This is supposed to make sure Metadata, Value, and Image objects only save if whole form passes
@permission_required('source_admin', (Source, 'id', 'source_id'))
def image_upload(request, source_id):
    """
    View for uploading images to a source.

    If one file in a multi-file upload fails to upload,
    none of the images in the upload are saved.
    """

    source = get_object_or_404(Source, id=source_id)
    uploadedImages = []

    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES, source=source)

        # TODO: Figure out why it's getting 500 (NoneType object is not subscriptable)
        # on certain combinations of files.  For example, bmp + cpc in one upload.
        if form.is_valid():

            encountered_error = False

            # Need getlist instead of simply request.FILES, in order to handle
            # multiple files.
            fileList = request.FILES.getlist('files')

            hasDataFromFilenames = form.cleaned_data['has_data_from_filenames']

            for file in fileList:

                filenameWithoutExtension = splitext(file.name)[0]

                if hasDataFromFilenames:

                    try:

                        # Make a generator of the metadata 'tokens' from the filename
                        tokens = (t for t in filenameWithoutExtension.split('_'))
                        metadataTokens = dict()

                        for keyIndex, valueIndex, valueClass in [
                                ('key1', 'value1', Value1),
                                ('key2', 'value2', Value2),
                                ('key3', 'value3', Value3),
                                ('key4', 'value4', Value4),
                                ('key5', 'value5', Value5) ]:

                            if getattr(source, keyIndex):
                                metadataTokens[valueIndex], created = valueClass.objects.get_or_create(name=tokens.next(), source=source)
                            else:
                                break  # Source has no more keys

                        #TODO: Consider an alternative to just filling in January 1:
                        # - use a date format that can be either year only, year and month
                        #   only, or year month and day (is such a format available)?
                        # - just require the month and day to be specified too
                        date_string = tokens.next()
                        year, month, day = date_string.split("-")
                        metadataTokens['photo_date'] = date(int(year), int(month), int(day))

                    #TODO: Have far more robust exception/error checking, which checks
                    # not just the filename parsing, but also the validity of the image files
                    # themselves.
                    # The idea is you need to call is_valid() with each file somehow,
                    # because it only checks one file per call.
                    # Perhaps this is a good time to jump ship and go with an AJAX form.
                    except (ValueError, StopIteration):
                        messages.error(request, 'Upload failed - Error when parsing the filename %s for metadata.' % file.name)
                        encountered_error = True
                        transaction.rollback()
                        uploadedImages = []
                        break

                    # Set the metadata
                    metadata = Metadata(name=filenameWithoutExtension,
                                        **metadataTokens)
#                    for paramName, paramValue in metadataTokens:
#                        setattr(metadata, paramName, paramValue)

                else:
                    metadata = Metadata(name=filenameWithoutExtension)
                    
                metadata.save()

                img = Image(original_file=file,
                        uploaded_by=request.user,
                        total_points=source.default_total_points,
                        metadata=metadata,
                        source=source)
                img.save()

                # Up to 5 uploaded images will be shown
                # upon successful upload
                uploadedImages.append(img)
                if len(uploadedImages) > 5:
                    uploadedImages = uploadedImages[1:]

            if not encountered_error:
                messages.success(request, '%d images uploaded.' % len(fileList))

        else:
            messages.error(request, 'Please correct the errors below.')


    # GET
    else:
        form = ImageUploadForm(source=source)

    #TODO: Show some kind of confirmation of the uploaded images.
    # (Maybe show a few samples)

    return render_to_response('images/image_upload.html', {
        'source': source,
        'imageUploadForm': form,
        'uploadedImages': uploadedImages
        },
        context_instance=RequestContext(request)
    )

# TODO: Make custom permission_required_blahblah decorators.
# For example, based on an image id, see if the user has permission to it. Make that permission_required_image.
#@permission_required('source_admin', (Source, 'id', 'Image.objects.get(pk=image_id).source.id'))
#def image_detail(request, image_id):
@permission_required('source_admin', (Source, 'id', 'source_id'))
def image_detail(request, image_id, source_id):
    """
    View for seeing an image's full size and details/metadata.
    """

    image = get_object_or_404(Image, id=image_id)
    #source = get_object_or_404(Source, Image.objects.get(pk=image_id).source.id)
    source = get_object_or_404(Source, id=source_id)

    # Fields to show on the detail page
    metadata = image.metadata

    return render_to_response('images/image_detail.html', {
        'source': source,
        'image': image,
        'metadata': metadata,
        },
        context_instance=RequestContext(request)
    )

@transaction.commit_on_success   # "Other" location values are only saved if form is error-less
@permission_required('source_admin', (Source, 'id', 'source_id'))
def image_detail_edit(request, image_id, source_id):
    """
    Edit image details.
    """

    image = get_object_or_404(Image, id=image_id)
    metadata = get_object_or_404(Metadata, id=image.metadata_id)
    source = get_object_or_404(Source, id=source_id)

    if request.method == 'POST':

        # Cancel
        cancel = request.POST.get('cancel', None)
        if cancel:
            messages.success(request, 'Edit cancelled.')
            return HttpResponseRedirect(reverse('image_detail', args=[source_id, image_id]))

        # Submit
        form = ImageDetailForm(request.POST, instance=metadata, source=source)

        if form.is_valid():
            form.save()
            messages.success(request, 'Image successfully edited.')
            return HttpResponseRedirect(reverse('image_detail', args=[source_id, image_id]))
        else:
            transaction.rollback()  # Don't save "Other" location values to database
            messages.error(request, 'Please correct the errors below.')
    else:
        # Just reached this form page
        form = ImageDetailForm(instance=metadata, source=source)

    return render_to_response('images/image_detail_edit.html', {
        'source': source,
        'image': image,
        'imageDetailForm': form,
        },
        context_instance=RequestContext(request)
        )

#TODO: check permissions
def import_labels(request, fileLocation)
    file = open(fileLocation, 'r') #opens the file for reading

    #iterates over each line in the file and processes it
    for line in file:
        #sanitizes and splits apart the string/line
        line = line.replace("; ", ';')
        words = line.split(';')

        #creates a label object and stores it in the database
        group = get_object_or_404(LabelGroup, name=words[2])
        label = Label(name=words[0], code=words[1], group=group)
        label.save()

    file.close() #closes file since we're done

def import_annotations(request, source_id, fileLocation)
    source = get_object_or_404(Source, id=source_id)
    file = open(fileLocation, 'r') #opens the file for reading
    count = 0 #keeps track of total points in one image
    prevImg = None #keeps track of the image processed on the previous iteration

    #iterate over each line in the file and processes it
    for line in file:
        #sanitizes and splits apart the string/line
        line = line.replace("; ", ';')
        words = line.split(';')

        #gets the 5 values that would describe the image
        value1 = get_object_or_404(Value1, name=words[0], source=source)
        value2 = get_object_or_404(Value2, name=words[1], source=source)
        value3 = get_object_or_404(Value3, name=words[2], source=source)
        value4 = get_object_or_404(Value4, name=words[3], source=source)
        value5 = get_object_or_404(Value5, name=words[4], source=source)

        #there should be one unique image that has the 5 values above, so get that image
        metadata = get_object_or_404(Metadata, value1=value1,
                                     value2=value2, value3=value3,
                                     value4=value4, value5=value5)
        image = get_object_or_404(Image, metadata=metadata)

        #check if this is the first image being processed
        if prevImg is None:
            prevImg = image

        #if the previous image was the same as this one, increment the point count
        if prevImg == image:
            count += 1
        else:
            count = 1

        prevImg = image

        #gets the label for the point, assumes it's already in the database
        label = get_object_or_404(Label, name=words[8])
        row = int(words[6])
        col = int(words[7])
        user = get_object_or_404(Profile, )

        #creates a point object and saves it in the database
        point = Point(row=row, col=col, point_number=count, image=image)
        point.save()

        #creates an annotation object and saves it in the database
        annotation = Annotation(annotation_date=datetime.now(), point=point, image=image,
                                user=user, label=label, source=source)
        annotation.save()

        #end for loop

    file.close() #closes the file since we're done