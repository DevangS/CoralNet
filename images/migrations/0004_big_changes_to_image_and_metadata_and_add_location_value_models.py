# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Value2'
        db.create_table('images_value2', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['images.Source'])),
        ))
        db.send_create_signal('images', ['Value2'])

        # Adding model 'Value1'
        db.create_table('images_value1', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['images.Source'])),
        ))
        db.send_create_signal('images', ['Value1'])

        # Adding model 'Value3'
        db.create_table('images_value3', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['images.Source'])),
        ))
        db.send_create_signal('images', ['Value3'])

        # Adding model 'Value4'
        db.create_table('images_value4', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['images.Source'])),
        ))
        db.send_create_signal('images', ['Value4'])

        # Adding model 'Value5'
        db.create_table('images_value5', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['images.Source'])),
        ))
        db.send_create_signal('images', ['Value5'])

        # Deleting field 'Metadata.width'
        db.delete_column('images_metadata', 'width')

        # Deleting field 'Metadata.height'
        db.delete_column('images_metadata', 'height')

        # Adding field 'Metadata.photo_date'
        db.add_column('images_metadata', 'photo_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True), keep_default=False)

        # Adding field 'Metadata.camera'
        db.add_column('images_metadata', 'camera', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'Metadata.strobes'
        db.add_column('images_metadata', 'strobes', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'Metadata.value1'
        db.add_column('images_metadata', 'value1', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['images.Value1'], null=True, blank=True), keep_default=False)

        # Adding field 'Metadata.value2'
        db.add_column('images_metadata', 'value2', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['images.Value2'], null=True, blank=True), keep_default=False)

        # Adding field 'Metadata.value3'
        db.add_column('images_metadata', 'value3', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['images.Value3'], null=True, blank=True), keep_default=False)

        # Adding field 'Metadata.value4'
        db.add_column('images_metadata', 'value4', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['images.Value4'], null=True, blank=True), keep_default=False)

        # Adding field 'Metadata.value5'
        db.add_column('images_metadata', 'value5', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['images.Value5'], null=True, blank=True), keep_default=False)

        # Adding field 'Metadata.group2_percent'
        db.add_column('images_metadata', 'group2_percent', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'Metadata.group1_percent'
        db.add_column('images_metadata', 'group1_percent', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'Metadata.group7_percent'
        db.add_column('images_metadata', 'group7_percent', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'Metadata.group6_percent'
        db.add_column('images_metadata', 'group6_percent', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'Metadata.group4_percent'
        db.add_column('images_metadata', 'group4_percent', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'Metadata.group5_percent'
        db.add_column('images_metadata', 'group5_percent', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'Metadata.group3_percent'
        db.add_column('images_metadata', 'group3_percent', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Changing field 'Metadata.pixel_cm_ratio'
        db.alter_column('images_metadata', 'pixel_cm_ratio', self.gf('django.db.models.fields.CharField')(max_length=45, null=True))

        # Changing field 'Metadata.description'
        db.alter_column('images_metadata', 'description', self.gf('django.db.models.fields.TextField')(max_length=1000))

        # Changing field 'Metadata.name'
        db.alter_column('images_metadata', 'name', self.gf('django.db.models.fields.CharField')(max_length=200))

        # Adding field 'Source.default_total_points'
        db.add_column('images_source', 'default_total_points', self.gf('django.db.models.fields.IntegerField')(default=50), keep_default=False)

        # Deleting field 'Image.camera'
        db.delete_column('images_image', 'camera_id')

        # Adding field 'Image.original_file'
        db.add_column('images_image', 'original_file', self.gf('django.db.models.fields.files.ImageField')(default='', max_length=100), keep_default=False)

        # Adding field 'Image.original_width'
        db.add_column('images_image', 'original_width', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'Image.original_height'
        db.add_column('images_image', 'original_height', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'Image.upload_date'
        db.add_column('images_image', 'upload_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, default=datetime.date(2000, 1, 1), blank=True), keep_default=False)

        # Adding field 'Image.uploaded_by'
        db.add_column('images_image', 'uploaded_by', self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['auth.User']), keep_default=False)

        # Adding field 'Image.metadata'
        db.add_column('images_image', 'metadata', self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['images.Metadata']), keep_default=False)


    def backwards(self, orm):
        
        # Deleting model 'Value2'
        db.delete_table('images_value2')

        # Deleting model 'Value1'
        db.delete_table('images_value1')

        # Deleting model 'Value3'
        db.delete_table('images_value3')

        # Deleting model 'Value4'
        db.delete_table('images_value4')

        # Deleting model 'Value5'
        db.delete_table('images_value5')

        # Adding field 'Metadata.width'
        db.add_column('images_metadata', 'width', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'Metadata.height'
        db.add_column('images_metadata', 'height', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Deleting field 'Metadata.photo_date'
        db.delete_column('images_metadata', 'photo_date')

        # Deleting field 'Metadata.camera'
        db.delete_column('images_metadata', 'camera')

        # Deleting field 'Metadata.strobes'
        db.delete_column('images_metadata', 'strobes')

        # Deleting field 'Metadata.value1'
        db.delete_column('images_metadata', 'value1_id')

        # Deleting field 'Metadata.value2'
        db.delete_column('images_metadata', 'value2_id')

        # Deleting field 'Metadata.value3'
        db.delete_column('images_metadata', 'value3_id')

        # Deleting field 'Metadata.value4'
        db.delete_column('images_metadata', 'value4_id')

        # Deleting field 'Metadata.value5'
        db.delete_column('images_metadata', 'value5_id')

        # Deleting field 'Metadata.group2_percent'
        db.delete_column('images_metadata', 'group2_percent')

        # Deleting field 'Metadata.group1_percent'
        db.delete_column('images_metadata', 'group1_percent')

        # Deleting field 'Metadata.group7_percent'
        db.delete_column('images_metadata', 'group7_percent')

        # Deleting field 'Metadata.group6_percent'
        db.delete_column('images_metadata', 'group6_percent')

        # Deleting field 'Metadata.group4_percent'
        db.delete_column('images_metadata', 'group4_percent')

        # Deleting field 'Metadata.group5_percent'
        db.delete_column('images_metadata', 'group5_percent')

        # Deleting field 'Metadata.group3_percent'
        db.delete_column('images_metadata', 'group3_percent')

        # Changing field 'Metadata.pixel_cm_ratio'
        db.alter_column('images_metadata', 'pixel_cm_ratio', self.gf('django.db.models.fields.IntegerField')(default=0))

        # Changing field 'Metadata.description'
        db.alter_column('images_metadata', 'description', self.gf('django.db.models.fields.CharField')(max_length=45))

        # Changing field 'Metadata.name'
        db.alter_column('images_metadata', 'name', self.gf('django.db.models.fields.CharField')(max_length=45))

        # Deleting field 'Source.default_total_points'
        db.delete_column('images_source', 'default_total_points')

        # Adding field 'Image.camera'
        db.add_column('images_image', 'camera', self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['images.Metadata']), keep_default=False)

        # Deleting field 'Image.original_file'
        db.delete_column('images_image', 'original_file')

        # Deleting field 'Image.original_width'
        db.delete_column('images_image', 'original_width')

        # Deleting field 'Image.original_height'
        db.delete_column('images_image', 'original_height')

        # Deleting field 'Image.upload_date'
        db.delete_column('images_image', 'upload_date')

        # Deleting field 'Image.uploaded_by'
        db.delete_column('images_image', 'uploaded_by_id')

        # Deleting field 'Image.metadata'
        db.delete_column('images_image', 'metadata_id')


    models = {
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
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Source']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'total_points': ('django.db.models.fields.IntegerField', [], {}),
            'upload_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'uploaded_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'images.metadata': {
            'Meta': {'object_name': 'Metadata'},
            'camera': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '1000', 'blank': 'True'}),
            'group1_percent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group2_percent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group3_percent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group4_percent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group5_percent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group6_percent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'group7_percent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'photo_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'photographer': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'pixel_cm_ratio': ('django.db.models.fields.CharField', [], {'max_length': '45', 'null': 'True', 'blank': 'True'}),
            'strobes': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'value1': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Value1']", 'null': 'True', 'blank': 'True'}),
            'value2': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Value2']", 'null': 'True', 'blank': 'True'}),
            'value3': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Value3']", 'null': 'True', 'blank': 'True'}),
            'value4': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Value4']", 'null': 'True', 'blank': 'True'}),
            'value5': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Value5']", 'null': 'True', 'blank': 'True'}),
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
            'default_total_points': ('django.db.models.fields.IntegerField', [], {}),
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
        }
    }

    complete_apps = ['images']
