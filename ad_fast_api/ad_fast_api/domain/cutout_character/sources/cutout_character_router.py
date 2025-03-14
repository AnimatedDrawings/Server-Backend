from fastapi import APIRouter, UploadFile, File
from ad_fast_api.workspace.sources import conf_workspace as cw
from ad_fast_api.snippets.sources.ad_http_exception import (
    handle_operation_async,
)
from ad_fast_api.domain.cutout_character.sources.features.cutout_character_feature import (
    save_cutout_image_async,
    configure_skeleton_async,
    create_cutout_character_response,
)
from ad_fast_api.snippets.sources.ad_logger import setup_logger
from ad_fast_api.domain.cutout_character.sources.cutout_character_schema import (
    CutoutCharacterResponse,
)


router = APIRouter()


@router.post("/cutout_character")
async def cutout_character(
    ad_id: str,
    file: UploadFile = File(...),
) -> CutoutCharacterResponse:
    base_path = cw.get_base_path(ad_id=ad_id)
    logger = setup_logger(base_path=base_path)

    await handle_operation_async(
        save_cutout_image_async,
        file=file,
        base_path=base_path,
        logger=logger,
        status_code=500,
    )

    char_cfg_dict = await handle_operation_async(
        configure_skeleton_async,
        base_path=base_path,
        logger=logger,
        status_code=501,
    )

    response = create_cutout_character_response(char_cfg_dict)
    return response


if __name__ == "__main__":
    import asyncio
    from io import BytesIO
    from unittest.mock import patch
    from ad_fast_api.workspace.request_files import reqeust_files as rf
    from ad_fast_api.domain.cutout_character.sources.features import configure_skeleton

    ad_id = rf.EXAMPLE1_AD_ID
    cutout_character_image_path = rf.EXAMPLE1_DIR_PATH.joinpath(
        rf.CUTOUT_CHARACTER_IMAGE_FILE_NAME
    )

    if not cutout_character_image_path.exists():
        raise FileNotFoundError(f"File not found: {cutout_character_image_path}")

    with open(cutout_character_image_path, "rb") as f:
        cutout_character_image_bytes = f.read()

    upload_file = UploadFile(
        filename=cutout_character_image_path.name,
        file=BytesIO(cutout_character_image_bytes),
    )

    with patch.object(
        configure_skeleton,
        "GET_SKELETON_TORCHSERVE_URL",
        new="http://localhost:8080/predictions/drawn_humanoid_pose_estimator",
    ):
        response = asyncio.run(
            cutout_character(
                ad_id=ad_id,
                file=upload_file,
            )
        )
        print(response.model_dump(mode="json"))


"""
torchserve-1         | 2025-03-14T02:54:35,770 [INFO ] epollEventLoopGroup-3-1 TS_METRICS - ts_inference_requests_total.Count:1.0|#model_name:drawn_humanoid_pose_estimator,model_version:default|#hostname:43741d2365a1,timestamp:1741920875
torchserve-1         | 2025-03-14T02:54:35,771 [DEBUG] W-9014-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd PREDICT repeats 1 to backend at: 1741920875771
torchserve-1         | 2025-03-14T02:54:35,771 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741920875771
torchserve-1         | 2025-03-14T02:54:35,772 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - load checkpoint from local path: /tmp/models/0ce6d86be5d34593a9f8761bfcf3c246/best_AP_epoch_72.pth
torchserve-1         | 2025-03-14T02:54:35,772 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Backend received inference at: 1741920875
torchserve-1         | 2025-03-14T02:54:35,900 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0-stdout org.pytorch.serve.wlm.WorkerLifeCycle - result=[METRICS]HandlerTime.Milliseconds:127.81|#ModelName:drawn_humanoid_pose_estimator,Level:Model|#type:GAUGE|#hostname:43741d2365a1,1741920875,4b039ec9-c32a-4693-9bf6-1635a4ebfb9c, pattern=[METRICS]
torchserve-1         | 2025-03-14T02:54:35,900 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0-stdout MODEL_METRICS - HandlerTime.ms:127.81|#ModelName:drawn_humanoid_pose_estimator,Level:Model|#hostname:43741d2365a1,requestID:4b039ec9-c32a-4693-9bf6-1635a4ebfb9c,timestamp:1741920875
torchserve-1         | 2025-03-14T02:54:35,900 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0-stdout org.pytorch.serve.wlm.WorkerLifeCycle - result=[METRICS]PredictionTime.Milliseconds:127.99|#ModelName:drawn_humanoid_pose_estimator,Level:Model|#type:GAUGE|#hostname:43741d2365a1,1741920875,4b039ec9-c32a-4693-9bf6-1635a4ebfb9c, pattern=[METRICS]
torchserve-1         | 2025-03-14T02:54:35,900 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0-stdout MODEL_METRICS - PredictionTime.ms:127.99|#ModelName:drawn_humanoid_pose_estimator,Level:Model|#hostname:43741d2365a1,requestID:4b039ec9-c32a-4693-9bf6-1635a4ebfb9c,timestamp:1741920875
torchserve-1         | 2025-03-14T02:54:35,901 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.BatchAggregator - Sending response for jobId 4b039ec9-c32a-4693-9bf6-1635a4ebfb9c
torchserve-1         | 2025-03-14T02:54:35,901 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0 ACCESS_LOG - /172.22.0.1:51644 "POST /predictions/drawn_humanoid_pose_estimator HTTP/1.1" 200 147
torchserve-1         | 2025-03-14T02:54:35,901 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0 TS_METRICS - Requests2XX.Count:1.0|#Level:Host|#hostname:43741d2365a1,timestamp:1741920875
torchserve-1         | 2025-03-14T02:54:35,901 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0 TS_METRICS - ts_inference_latency_microseconds.Microseconds:130260.573|#model_name:drawn_humanoid_pose_estimator,model_version:default|#hostname:43741d2365a1,timestamp:1741920875
torchserve-1         | 2025-03-14T02:54:35,901 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0 TS_METRICS - ts_queue_latency_microseconds.Microseconds:130.746|#model_name:drawn_humanoid_pose_estimator,model_version:default|#hostname:43741d2365a1,timestamp:1741920875
torchserve-1         | 2025-03-14T02:54:35,902 [DEBUG] W-9014-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.job.RestJob - Waiting time ns: 130746, Backend time ns: 130946133
torchserve-1         | 2025-03-14T02:54:35,902 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0 TS_METRICS - QueueTime.Milliseconds:0.0|#Level:Host|#hostname:43741d2365a1,timestamp:1741920875
torchserve-1         | 2025-03-14T02:54:35,902 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 130
torchserve-1         | 2025-03-14T02:54:35,902 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:1.0|#Level:Host|#hostname:43741d2365a1,timestamp:1741920875

"""
