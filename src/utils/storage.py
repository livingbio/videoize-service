from django.core.files.storage import get_storage_class

from django_hashedfilenamestorage.storage import HashedFilenameMetaStorage

HashedFilenameMyStorage = HashedFilenameMetaStorage(
    storage_class=get_storage_class('gcs_storage.storage.GoogleCloudStorage'),
)
