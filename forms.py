from django.forms.fields import CharField

class FormHelper():
    
    @staticmethod
    def stripSpacesFromFields(data, fields):
        """
        Use this in the clean() method of a Form subclass.  Pass in
        two form attributes as the arguments: cleaned_data and fields.

        This will go through each form field and strip spaces if it's a
        CharField or a descendant of CharField (EmailField, etc.).
        (To see what these descendants are, see django/forms/fields.py.)
        """
        for fieldName, value in data.items():
            if isinstance(fields[fieldName], CharField):
                data[fieldName] = value.strip()
        return data
