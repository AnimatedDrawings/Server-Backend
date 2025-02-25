import yaml
from ad_fast_api.snippets.sources.save_dict import (
    dict_to_file,
    file_to_dict,
)
from ad_fast_api.snippets.testings.ad_test.ad_test_helper import measure_execution_time


def test_file_to_dict(tmp_path):
    # 테스트용 YAML 데이터 정의
    data = {"name": "test", "values": [1, 2, 3]}
    test_file = tmp_path / "test_file.yaml"

    # YAML 데이터를 파일에 저장
    with open(test_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f)

    # 파일을 읽어서 딕셔너리로 변환하는지 테스트
    result = measure_execution_time("file_to_dict")(file_to_dict)(file_path=test_file)
    assert result == data


def test_dict_to_file(tmp_path):
    # 저장할 데이터 정의
    data = {"version": 1.0, "active": True}
    test_file = tmp_path / "output.yaml"

    # 데이터 dic -> 파일 저장 수행
    measure_execution_time("dict_to_file")(dict_to_file)(
        to_save_dict=data,
        file_path=test_file,
    )

    # 저장된 파일을 직접 읽어 yaml 데이터를 검증
    with open(test_file, "r", encoding="utf-8") as f:
        loaded_data = yaml.load(f, Loader=yaml.FullLoader)
    assert loaded_data == data


def test_round_trip(tmp_path):
    # dict_to_file와 file_to_dict 함수가 정상적으로 동작하는지
    # round-trip 테스트 (저장 후 다시 로드) 수행
    original_data = {
        "nested": {
            "a": 1,
            "b": "hello",
            "c": [1, 2, 3],
        },
        "flag": False,
    }
    test_file = tmp_path / "roundtrip.yaml"

    dict_to_file(original_data, test_file)
    loaded_data = file_to_dict(test_file)
    assert loaded_data == original_data
