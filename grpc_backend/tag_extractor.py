import pydicom

def extract_dicom_tags_old(file_path, tag_list):
    ds = pydicom.dcmread(file_path)
    result = {}
    for tag in tag_list:
        tag_str = f'{tag[0]},{tag[1]}'
        try:
            data_element = ds.get(tag, None)
            if data_element is not None:
                result[tag_str] = {"name": data_element.name, "value": str(data_element.value)}
            else:
                result[tag_str] = {"error": "Tag not found"}
        except Exception as e:
            result[tag_str] = {"error": str(e)}
    return result



