# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    depends_on = (
        ("guardian", "0005_auto__chg_field_groupobjectpermission_object_pk__chg_field_userobjectp"),
    )

    def forwards(self, orm):
        print "-----"
        print "This migration will create the Source View and Edit"
        print "permission types, if they don't already exist in the"
        print "auth system."
        print ""

        try:
            ct = orm['contenttypes.ContentType'].objects.get(model='source', app_label='images') # model must be lowercase
        except orm['contenttypes.ContentType'].DoesNotExist:
            print "Didn't find a ContentType for the Source model, so we can deduce"
            print "that the Source model has just been created during this series"
            print "of migration runs.  The Admin, Edit, and View permissions"
            print "should be auto-created later along with the Source"
            print "model.  No need to do anything in this migration."
        else:
            view_perm, created = orm['auth.permission'].objects.get_or_create(
                content_type=ct, codename=u'source_view', defaults={'name': u'View'})
            if created:
                print "Source View permission type created."
            else:
                print "Source View permission type already exists."

            edit_perm, created = orm['auth.permission'].objects.get_or_create(
                content_type=ct, codename=u'source_edit', defaults={'name': u'Edit'})
            if created:
                print "Source Edit permission type created."
            else:
                print "Source Edit permission type already exists."

            print "Next, we'll grant View and Edit permissions for all current Source Admins."
            print "NOTE: If you have any orphaned object permissions (permission to a source that doesn't exist), this might fail. To clean up those orphaned permissions, try:"
            print "./manage.py clean_orphan_obj_perms"

            admin_perm = orm['auth.permission'].objects.get(content_type=ct, codename=u'source_admin')

            for p in orm['guardian.userobjectpermission'].objects.filter(permission=admin_perm):
                source = orm['images.source'].objects.get(pk=p.object_pk)

                view_userobjperm, created = orm['guardian.userobjectpermission'].objects.get_or_create(
                    permission=view_perm, object_pk=p.object_pk, user=p.user, content_type=ct)
                if created:
                    print "User %s has been granted View permission for Source %s." % (p.user.username, source.name)
                else:
                    print "User %s already has View permission for Source %s." % (p.user.username, source.name)

                edit_userobjperm, created = orm['guardian.userobjectpermission'].objects.get_or_create(
                    permission=edit_perm, object_pk=p.object_pk, user=p.user, content_type=ct)
                if created:
                    print "User %s has been granted Edit permission for Source %s." % (p.user.username, source.name)
                else:
                    print "User %s already has Edit permission for Source %s." % (p.user.username, source.name)

            print "Done granting permissions."

        print "-----"


    def backwards(self, orm):
        print "-----"
        print "NOTE: This backwards migration will remove all instances of the View and Edit Source permissions in the database."

        ct = orm['contenttypes.ContentType'].objects.get(model='source', app_label='images') # model must be lowercase

        view_perm = orm['auth.permission'].objects.get(content_type=ct, codename=u'source_view')
        edit_perm = orm['auth.permission'].objects.get(content_type=ct, codename=u'source_edit')

        for p in orm['guardian.userobjectpermission'].objects.filter(permission=view_perm, content_type=ct):
            source = orm['images.source'].objects.get(pk=p.object_pk)
            p.delete()
            print "User %s's View permission for Source %s has been removed." % (p.user.username, source.name)

        for p in orm['guardian.userobjectpermission'].objects.filter(permission=edit_perm, content_type=ct):
            source = orm['images.source'].objects.get(pk=p.object_pk)
            p.delete()
            print "User %s's Edit permission for Source %s has been removed." % (p.user.username, source.name)

        view_perm.delete()
        print "Removed the View Source permission type."
        edit_perm.delete()
        print "Removed the Edit Source permission type."

        print "Done."
        print "-----"


    models = {
        'annotations.label': {
            'Meta': {'object_name': 'Label'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['annotations.LabelGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True'})
        },
        'annotations.labelgroup': {
            'Meta': {'object_name': 'LabelGroup'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'})
        },
        'annotations.labelset': {
            'Meta': {'object_name': 'LabelSet'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'edit_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'labels': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['annotations.Label']", 'symmetrical': 'False'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'images.image': {
            'Meta': {'object_name': 'Image'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metadata': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Metadata']"}),
            'original_file': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'original_height': ('django.db.models.fields.IntegerField', [], {}),
            'original_width': ('django.db.models.fields.IntegerField', [], {}),
            'point_generation_method': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Source']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'upload_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'uploaded_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'images.metadata': {
            'Meta': {'object_name': 'Metadata'},
            'balance': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'camera': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'comments': ('django.db.models.fields.TextField', [], {'max_length': '1000', 'blank': 'True'}),
            'depth': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'framing': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'group1_percent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group2_percent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group3_percent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group4_percent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group5_percent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group6_percent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group7_percent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'photo_date': ('django.db.models.fields.DateField', [], {}),
            'photographer': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'pixel_cm_ratio': ('django.db.models.fields.CharField', [], {'max_length': '45', 'null': 'True', 'blank': 'True'}),
            'strobes': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'value1': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Value1']", 'null': 'True'}),
            'value2': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Value2']", 'null': 'True'}),
            'value3': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Value3']", 'null': 'True'}),
            'value4': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Value4']", 'null': 'True'}),
            'value5': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Value5']", 'null': 'True'}),
            'water_quality': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'})
        },
        'images.point': {
            'Meta': {'object_name': 'Point'},
            'annotation_status': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'column': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Image']"}),
            'point_number': ('django.db.models.fields.IntegerField', [], {}),
            'row': ('django.db.models.fields.IntegerField', [], {})
        },
        'images.source': {
            'Meta': {'object_name': 'Source'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default_point_generation_method': ('django.db.models.fields.CharField', [], {'default': "'m_200'", 'max_length': '50'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key1': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'key2': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'key3': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'key4': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'key5': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'labelset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['annotations.LabelSet']"}),
            'latitude': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'visibility': ('django.db.models.fields.CharField', [], {'default': "'v'", 'max_length': '1'})
        },
        'images.value1': {
            'Meta': {'object_name': 'Value1'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Source']"})
        },
        'images.value2': {
            'Meta': {'object_name': 'Value2'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Source']"})
        },
        'images.value3': {
            'Meta': {'object_name': 'Value3'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Source']"})
        },
        'images.value4': {
            'Meta': {'object_name': 'Value4'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Source']"})
        },
        'images.value5': {
            'Meta': {'object_name': 'Value5'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Source']"})
        },
        'guardian.userobjectpermission': {
            'Meta': {'unique_together': "(['user', 'permission', 'content_type', 'object_pk'],)", 'object_name': 'UserObjectPermission'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_pk': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'permission': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Permission']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['images']
