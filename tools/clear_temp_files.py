import os
import shutil
import tempfile


def clear_temp_files():
    temp_path = tempfile.gettempdir()

    deleted_files = 0
    deleted_folders = 0
    skipped_items = 0
    freed_space_bytes = 0

    for item in os.listdir(temp_path):
        item_path = os.path.join(temp_path, item)

        try:
            # Delete files
            if os.path.isfile(item_path):
                freed_space_bytes += os.path.getsize(item_path)
                os.remove(item_path)
                deleted_files += 1

            # Delete folders
            elif os.path.isdir(item_path):
                folder_size = 0

                for root, dirs, files in os.walk(item_path):
                    for file in files:
                        file_path = os.path.join(root, file)

                        try:
                            folder_size += os.path.getsize(file_path)
                        except:
                            pass

                shutil.rmtree(item_path)

                freed_space_bytes += folder_size
                deleted_folders += 1

        except:
            skipped_items += 1

    freed_space_mb = round(freed_space_bytes / (1024 * 1024), 2)

    return {
        "status": "success",
        "temp_path": temp_path,
        "deleted_files": deleted_files,
        "deleted_folders": deleted_folders,
        "skipped_items": skipped_items,
        "freed_space_mb": freed_space_mb
    }


# Testing
result = clear_temp_files()

print("TEMP FILE CLEANUP")
print(f"Temp Path        : {result['temp_path']}")
print(f"Deleted Files    : {result['deleted_files']}")
print(f"Deleted Folders  : {result['deleted_folders']}")
print(f"Skipped Items    : {result['skipped_items']}")
print(f"Freed Space      : {result['freed_space_mb']} MB")

