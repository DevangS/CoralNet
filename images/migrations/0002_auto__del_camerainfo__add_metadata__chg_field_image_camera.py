# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'CameraInfo'
        db.delete_table('images_camerainfo')

        # Adding model 'Metadata'
        db.create_table('images_metadata', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
            ('pixel_cm_ratio', self.gf('django.db.models.fields.IntegerField')()),
            ('height', self.gf('django.db.models.fields.IntegerField')()),
            ('width', self.gf('django.db.models.fields.IntegerField')()),
            ('photographer', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
            ('water_quality', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
        ))
        db.send_create_signal('images', ['Metadata'])

        # Changing field 'Image.camera'
        db.alter_column('images_image', 'camera_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['images.Metadata']))


    def backwards(self, orm):
        
        # Adding model 'CameraInfo'
        db.create_table('images_camerainfo', (
            ('pixel_cm_ratio', self.gf('django.db.models.fields.IntegerField')()),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
            ('width', self.gf('django.db.models.fields.IntegerField')()),
            ('photographer', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
            ('water_quality', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('height', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('images', ['CameraInfo'])

        # Deleting model 'Metadata'
        db.delete_table('images_metadata')

        # Changing field 'Image.camera'
        db.alter_column('images_image', 'camera_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['images.CameraInfo']))


    models = {
        'images.image': {
            'Meta': {'object_name': 'Image'},
            'camera': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Metadata']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Source']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'total_points': ('django.db.models.fields.IntegerField', [], {})
        },
        'images.metadata': {
            'Meta': {'object_name': 'Metadata'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'height': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'photographer': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'pixel_cm_ratio': ('django.db.models.fields.IntegerField', [], {}),
            'water_quality': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'width': ('django.db.models.fields.IntegerField', [], {})
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
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key1': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'key2': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'key3': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'key4': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'key5': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'latitude': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'visibility': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        }
    }

    complete_apps = ['images']
