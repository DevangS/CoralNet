# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):

        print (
            "-----\n"
            "This migration sets source-level annotation areas for sources that don't\n"
            "have this field set yet.\n"
            "...\n"
        )

        # Hardcode the default string; don't use the utils function to create the string.
        # Otherwise, changing the db string format later would cause this migration's behavior
        # to change, which might not be good.
        defaultAnnotationArea = '0,100,0,100'

        numSourcesChanged = 0
        sourcesWithoutAnnotationArea = orm.Source.objects.filter(image_annotation_area__isnull=True)

        for source in sourcesWithoutAnnotationArea:
            source.image_annotation_area = defaultAnnotationArea
            source.save()
            numSourcesChanged += 1

        print (
            "%s sources set with a source-level annotation area of 0-100%% X, 0-100%% Y.\n"
            "-----" % numSourcesChanged
        )


    def backwards(self, orm):

        print (
            "-----\n"
            "This migration rollback doesn't do anything; we don't know which\n"
            "sources had annotation areas set before, so we can't un-set those annotation areas.\n"
            "-----"
        )


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
            'latest_robot_annotator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Robot']", 'null': 'True'}),
            'metadata': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Metadata']"}),
            'original_file': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'original_height': ('django.db.models.fields.IntegerField', [], {}),
            'original_width': ('django.db.models.fields.IntegerField', [], {}),
            'point_generation_method': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'process_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Source']"}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.ImageStatus']"}),
            'upload_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'uploaded_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'images.imagestatus': {
            'Meta': {'object_name': 'ImageStatus'},
            'annotatedByHuman': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'annotatedByRobot': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'featuresExtracted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hasRandomPoints': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'preprocessed': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'images.metadata': {
            'Meta': {'object_name': 'Metadata'},
            'annotation_area': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
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
            'height_in_cm': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'photo_date': ('django.db.models.fields.DateField', [], {}),
            'photographer': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
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
        'images.robot': {
            'Meta': {'object_name': 'Robot'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path_to_model': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Source']"}),
            'time_to_train': ('django.db.models.fields.BigIntegerField', [], {}),
            'version': ('django.db.models.fields.IntegerField', [], {'unique': 'True'})
        },
        'images.source': {
            'Meta': {'object_name': 'Source'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default_point_generation_method': ('django.db.models.fields.CharField', [], {'default': "'m_200'", 'max_length': '50'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_annotation_area': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'image_height_in_cm': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
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
        'images.sourceinvite': {
            'Meta': {'unique_together': "(['recipient', 'source'],)", 'object_name': 'SourceInvite'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invites_received'", 'to': "orm['auth.User']"}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invites_sent'", 'to': "orm['auth.User']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Source']"}),
            'source_perm': ('django.db.models.fields.CharField', [], {'max_length': '50'})
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
        }
    }

    complete_apps = ['images']
