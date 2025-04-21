import io
from pathlib import Path

fake_workspace_files_path = Path(__file__).parent
fake_log_file_name = "test.log"
fake_ad_id = "test_ad_id"
fake_test_file = io.BytesIO(b"fake image content")
fake_upload_file = {"file": ("test.png", fake_test_file, "image/png")}
