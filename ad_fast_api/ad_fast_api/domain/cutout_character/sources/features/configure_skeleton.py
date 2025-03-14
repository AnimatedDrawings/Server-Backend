import cv2
import numpy as np
from cv2.typing import MatLike
import httpx
from typing import Optional
from ad_fast_api.domain.cutout_character.sources.errors import (
    cutout_character_500_status as cc5s,
)
from ad_fast_api.workspace.sources import conf_workspace as cw
from logging import Logger
import json
from pathlib import Path
from ad_fast_api.workspace.sources.conf_workspace import CHAR_CFG_FILE_NAME
from ad_fast_api.snippets.sources.save_dict import dict_to_file


GET_SKELETON_TORCHSERVE_URL = (
    "http://torchserve:8080/predictions/drawn_humanoid_pose_estimator"
)


def get_cropped_image(
    base_path: Path,
    logger: Logger,
):
    cropped_image_path = base_path / cw.CROPPED_IMAGE_NAME
    cropped_image = cv2.imread(cropped_image_path.as_posix())
    if cropped_image is None:
        msg = cc5s.NOT_FOUND_CROPPED_IMAGE.format(cropped_image_path=cropped_image_path)
        logger.critical(msg)
        raise Exception(msg)

    return cropped_image


async def get_pose_result_async(
    cropped_image,
    logger: Logger,
    url: Optional[str] = None,
) -> list[dict] | dict:
    img_b = cv2.imencode(".png", cropped_image)[1].tobytes()
    request_data = {"data": img_b}

    async with httpx.AsyncClient(verify=False) as client:
        try:
            resp = await client.post(
                url or GET_SKELETON_TORCHSERVE_URL,
                files=request_data,
            )
        except Exception as e:
            msg = cc5s.GET_SKELETON_TORCHSERVE_ERROR.format(resp=str(e))
            logger.critical(msg)
            raise Exception(msg)

        if resp is None or resp.status_code >= 300:
            msg = cc5s.GET_SKELETON_TORCHSERVE_ERROR.format(resp=resp)
            logger.critical(msg)
            raise Exception(msg)

        pose_results = json.loads(resp.content)
        return pose_results


def get_pose_result(
    cropped_image: MatLike,
    logger: Logger,
    url: Optional[str] = None,
) -> list[dict] | dict:
    data_file = {"data": cv2.imencode(".png", cropped_image)[1].tobytes()}
    with httpx.Client(verify=False) as client:
        try:
            resp = client.post(
                url or GET_SKELETON_TORCHSERVE_URL,
                files=data_file,
            )
        except Exception as e:
            msg = cc5s.GET_SKELETON_TORCHSERVE_ERROR.format(resp=str(e))
            logger.critical(msg)
            raise Exception(msg)

        if resp is None or resp.status_code >= 300:
            msg = cc5s.GET_SKELETON_TORCHSERVE_ERROR.format(resp=resp)
            logger.critical(msg)
            raise Exception(msg)

        pose_results = json.loads(resp.content)
        return pose_results


def check_pose_results(
    pose_results: list[dict] | dict,
    logger: Logger,
) -> np.ndarray:
    if (
        type(pose_results) == dict
        and "code" in pose_results.keys()
        and pose_results["code"] == 404
    ):
        msg = cc5s.POSE_ESTIMATION_ERROR.format(pose_results=pose_results)
        logger.critical(msg)
        raise Exception(msg)

    # if cannot detect any skeleton, abort
    if len(pose_results) == 0:
        msg = cc5s.NO_SKELETON_DETECTED
        logger.critical(msg)
        raise Exception(msg)

    # if more than one skeleton detected, abort
    if 1 < len(pose_results):
        msg = cc5s.MORE_THAN_ONE_SKELETON_DETECTED.format(
            len_pose_results=len(pose_results)
        )
        logger.critical(msg)
        raise Exception(msg)

    # get x y coordinates of detection joint keypoints
    kpts = np.array(pose_results[0]["keypoints"])[:, :2]
    return kpts


def make_skeleton(
    kpts: np.ndarray,
) -> list:
    # use them to build character skeleton rig
    skeleton = []
    skeleton.append(
        {
            "loc": [round(x) for x in (kpts[11] + kpts[12]) / 2],
            "name": "root",
            "parent": None,
        }
    )
    skeleton.append(
        {
            "loc": [round(x) for x in (kpts[11] + kpts[12]) / 2],
            "name": "hip",
            "parent": "root",
        }
    )
    skeleton.append(
        {
            "loc": [round(x) for x in (kpts[5] + kpts[6]) / 2],
            "name": "torso",
            "parent": "hip",
        }
    )
    skeleton.append(
        {"loc": [round(x) for x in kpts[0]], "name": "neck", "parent": "torso"}
    )
    skeleton.append(
        {
            "loc": [round(x) for x in kpts[6]],
            "name": "right_shoulder",
            "parent": "torso",
        }
    )
    skeleton.append(
        {
            "loc": [round(x) for x in kpts[8]],
            "name": "right_elbow",
            "parent": "right_shoulder",
        }
    )
    skeleton.append(
        {
            "loc": [round(x) for x in kpts[10]],
            "name": "right_hand",
            "parent": "right_elbow",
        }
    )
    skeleton.append(
        {"loc": [round(x) for x in kpts[5]], "name": "left_shoulder", "parent": "torso"}
    )
    skeleton.append(
        {
            "loc": [round(x) for x in kpts[7]],
            "name": "left_elbow",
            "parent": "left_shoulder",
        }
    )
    skeleton.append(
        {
            "loc": [round(x) for x in kpts[9]],
            "name": "left_hand",
            "parent": "left_elbow",
        }
    )
    skeleton.append(
        {"loc": [round(x) for x in kpts[12]], "name": "right_hip", "parent": "root"}
    )
    skeleton.append(
        {
            "loc": [round(x) for x in kpts[14]],
            "name": "right_knee",
            "parent": "right_hip",
        }
    )
    skeleton.append(
        {
            "loc": [round(x) for x in kpts[16]],
            "name": "right_foot",
            "parent": "right_knee",
        }
    )
    skeleton.append(
        {"loc": [round(x) for x in kpts[11]], "name": "left_hip", "parent": "root"}
    )
    skeleton.append(
        {"loc": [round(x) for x in kpts[13]], "name": "left_knee", "parent": "left_hip"}
    )
    skeleton.append(
        {
            "loc": [round(x) for x in kpts[15]],
            "name": "left_foot",
            "parent": "left_knee",
        }
    )

    return skeleton


def save_char_cfg(
    skeleton: list,
    cropped_image: MatLike,
    base_path: Path,
) -> dict:
    # create the character config dictionary
    char_cfg = {
        "skeleton": skeleton,
        "height": cropped_image.shape[0],
        "width": cropped_image.shape[1],
    }
    char_cfg_path = base_path.joinpath(CHAR_CFG_FILE_NAME)
    dict_to_file(
        to_save_dict=char_cfg,
        file_path=char_cfg_path,
    )

    return char_cfg


# if __name__ == "__main__":
#     import asyncio
#     from ad_fast_api.workspace.testings.request_files import mock_conf_workspace as mcw
#     from ad_fast_api.workspace.sources import conf_workspace as cw
#     from ad_fast_api.snippets.sources.ad_logger import setup_logger

#     base_path = mcw.TMP_WORKSPACE_FILES
#     request_files_path = mcw.REQUEST_FILES_PATH
#     logger = setup_logger(base_path=base_path)

#     url = "http://localhost:8080/predictions/drawn_humanoid_pose_estimator"
#     cropped_image_path = request_files_path / cw.CROPPED_IMAGE_NAME
#     cropped_image = get_cropped_image(
#         base_path=base_path,
#         logger=logger,
#     )

#     response = get_pose_result(
#         cropped_image=cropped_image,
#         logger=logger,
#         url=url,
#     )

#     # response = asyncio.run(
#     #     get_pose_result_async(
#     #         cropped_image=cropped_image,
#     #         logger=logger,
#     #         url=url,
#     #     ),
#     # )

#     print(response)


# """
# 2025-03-13T06:40:23,345 [INFO ] epollEventLoopGroup-3-1 TS_METRICS - ts_inference_requests_total.Count:1.0|#model_name:drawn_humanoid_pose_estimator,model_version:default|#hostname:a4b121b5827f,timestamp:1741848023
# 2025-03-13T06:40:23,346 [DEBUG] W-9015-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd PREDICT repeats 1 to backend at: 1741848023346
# 2025-03-13T06:40:23,346 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848023346
# 2025-03-13T06:40:23,347 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - load checkpoint from local path: /tmp/models/ae3ebd10fc1b498c93a89b1816e98824/best_AP_epoch_72.pth
# 2025-03-13T06:40:23,347 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Backend received inference at: 1741848023
# 2025-03-13T06:40:23,471 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0-stdout org.pytorch.serve.wlm.WorkerLifeCycle - result=[METRICS]HandlerTime.Milliseconds:123.37|#ModelName:drawn_humanoid_pose_estimator,Level:Model|#type:GAUGE|#hostname:a4b121b5827f,1741848023,3c53ef2a-5a1e-4e46-9fbf-6a5711049eb7, pattern=[METRICS]
# 2025-03-13T06:40:23,471 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0-stdout MODEL_METRICS - HandlerTime.ms:123.37|#ModelName:drawn_humanoid_pose_estimator,Level:Model|#hostname:a4b121b5827f,requestID:3c53ef2a-5a1e-4e46-9fbf-6a5711049eb7,timestamp:1741848023
# 2025-03-13T06:40:23,471 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0-stdout org.pytorch.serve.wlm.WorkerLifeCycle - result=[METRICS]PredictionTime.Milliseconds:123.52|#ModelName:drawn_humanoid_pose_estimator,Level:Model|#type:GAUGE|#hostname:a4b121b5827f,1741848023,3c53ef2a-5a1e-4e46-9fbf-6a5711049eb7, pattern=[METRICS]
# 2025-03-13T06:40:23,471 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0-stdout MODEL_METRICS - PredictionTime.ms:123.52|#ModelName:drawn_humanoid_pose_estimator,Level:Model|#hostname:a4b121b5827f,requestID:3c53ef2a-5a1e-4e46-9fbf-6a5711049eb7,timestamp:1741848023
# 2025-03-13T06:40:23,471 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.BatchAggregator - Sending response for jobId 3c53ef2a-5a1e-4e46-9fbf-6a5711049eb7
# 2025-03-13T06:40:23,472 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0 ACCESS_LOG - /172.22.0.1:39158 "POST /predictions/drawn_humanoid_pose_estimator HTTP/1.1" 200 144
# 2025-03-13T06:40:23,472 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0 TS_METRICS - Requests2XX.Count:1.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848023
# 2025-03-13T06:40:23,473 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0 TS_METRICS - ts_inference_latency_microseconds.Microseconds:125904.592|#model_name:drawn_humanoid_pose_estimator,model_version:default|#hostname:a4b121b5827f,timestamp:1741848023
# 2025-03-13T06:40:23,473 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0 TS_METRICS - ts_queue_latency_microseconds.Microseconds:141.004|#model_name:drawn_humanoid_pose_estimator,model_version:default|#hostname:a4b121b5827f,timestamp:1741848023
# 2025-03-13T06:40:23,473 [DEBUG] W-9015-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.job.RestJob - Waiting time ns: 141004, Backend time ns: 126824820
# 2025-03-13T06:40:23,473 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0 TS_METRICS - QueueTime.Milliseconds:0.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848023
# 2025-03-13T06:40:23,473 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 125
# 2025-03-13T06:40:23,473 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:2.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848023

# """


# """
# Removing orphan pid file.
# WARNING: sun.reflect.Reflection.getCallerClass is not supported. This will impact performance.
# nvidia-smi not available or failed: Cannot run program "nvidia-smi": error=2, No such file or directory
# 2025-03-13T06:41:48,936 [DEBUG] main org.pytorch.serve.util.ConfigManager - xpu-smi not available or failed: Cannot run program "xpu-smi": error=2, No such file or directory
# 2025-03-13T06:41:48,941 [WARN ] main org.pytorch.serve.util.ConfigManager - Your torchserve instance can access any URL to load models. When deploying to production, make sure to limit the set of allowed_urls in config.properties
# 2025-03-13T06:41:48,953 [INFO ] main org.pytorch.serve.servingsdk.impl.PluginsManager - Initializing plugins manager...
# 2025-03-13T06:41:49,012 [INFO ] main org.pytorch.serve.metrics.configuration.MetricConfiguration - Successfully loaded metrics configuration from /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml
# 2025-03-13T06:41:49,179 [INFO ] main org.pytorch.serve.ModelServer -
# Torchserve version: 0.12.0
# TS Home: /opt/conda/lib/python3.8/site-packages
# Current directory: /
# Temp directory: /tmp
# Metrics config path: /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml
# Number of GPUs: 0
# Number of CPUs: 16
# Max heap size: 15036 M
# Python executable: /opt/conda/bin/python
# Config file: /home/torchserve/config.properties
# Inference address: http://0.0.0.0:8080
# Management address: http://0.0.0.0:8081
# Metrics address: http://0.0.0.0:8082
# Model Store: /home/torchserve/model-store
# Initial Models: all
# Log dir: /logs
# Metrics dir: /logs
# Netty threads: 0
# Netty client threads: 0
# Default workers per model: 16
# Blacklist Regex: N/A
# Maximum Response Size: 6553500
# Maximum Request Size: 6553500
# Limit Maximum Image Pixels: true
# Prefer direct buffer: false
# Allowed Urls: [file://.*|http(s)?://.*]
# Custom python dependency for model allowed: false
# Enable metrics API: true
# Metrics mode: LOG
# Disable system metrics: false
# Workflow Store: /home/torchserve/model-store
# CPP log config: N/A
# Model config: N/A
# System metrics command: default
# Model API enabled: false
# 2025-03-13T06:41:49,200 [INFO ] main org.pytorch.serve.servingsdk.impl.PluginsManager -  Loading snapshot serializer plugin...
# 2025-03-13T06:41:49,237 [DEBUG] main org.pytorch.serve.ModelServer - Loading models from model store: drawn_humanoid_pose_estimator.mar
# 2025-03-13T06:41:53,303 [DEBUG] main org.pytorch.serve.wlm.ModelVersionedRefs - Adding new version 1.0 for model drawn_humanoid_pose_estimator
# 2025-03-13T06:41:53,303 [DEBUG] main org.pytorch.serve.wlm.ModelVersionedRefs - Setting default version to 1.0 for model drawn_humanoid_pose_estimator
# 2025-03-13T06:41:53,303 [INFO ] main org.pytorch.serve.wlm.ModelManager - Model drawn_humanoid_pose_estimator loaded.
# 2025-03-13T06:41:53,303 [DEBUG] main org.pytorch.serve.wlm.ModelManager - updateModel: drawn_humanoid_pose_estimator, count: 16
# 2025-03-13T06:41:53,326 [DEBUG] main org.pytorch.serve.ModelServer - Loading models from model store: drawn_humanoid_detector.mar
# 2025-03-13T06:41:53,326 [DEBUG] W-9003-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9003, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:53,326 [DEBUG] W-9010-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9010, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:53,312 [DEBUG] W-9009-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9009, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:53,312 [DEBUG] W-9007-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9007, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:53,312 [DEBUG] W-9002-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9002, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:53,326 [DEBUG] W-9004-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9004, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:53,326 [DEBUG] W-9006-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9006, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:53,312 [DEBUG] W-9000-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9000, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:53,326 [DEBUG] W-9013-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9013, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:53,326 [DEBUG] W-9001-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9001, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:53,327 [DEBUG] W-9005-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9005, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:53,327 [DEBUG] W-9014-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9014, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:53,327 [DEBUG] W-9011-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9011, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:53,327 [DEBUG] W-9015-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9015, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:53,327 [DEBUG] W-9012-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9012, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:53,327 [DEBUG] W-9008-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9008, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:55,713 [INFO ] W-9010-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9010, pid=97
# 2025-03-13T06:41:55,713 [INFO ] W-9012-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9012, pid=95
# 2025-03-13T06:41:55,717 [INFO ] W-9010-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9010
# 2025-03-13T06:41:55,714 [INFO ] W-9004-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9004, pid=74
# 2025-03-13T06:41:55,722 [INFO ] W-9004-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9004
# 2025-03-13T06:41:55,714 [INFO ] W-9009-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9009, pid=73
# 2025-03-13T06:41:55,723 [INFO ] W-9009-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9009
# 2025-03-13T06:41:55,713 [INFO ] W-9013-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9013, pid=102
# 2025-03-13T06:41:55,724 [INFO ] W-9009-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:41:55,715 [INFO ] W-9006-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9006, pid=101
# 2025-03-13T06:41:55,721 [INFO ] W-9007-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9007, pid=72
# 2025-03-13T06:41:55,721 [INFO ] W-9000-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9000, pid=94
# 2025-03-13T06:41:55,728 [INFO ] W-9004-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:41:55,719 [INFO ] W-9011-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9011, pid=100
# 2025-03-13T06:41:55,717 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9014, pid=92
# 2025-03-13T06:41:55,717 [INFO ] W-9002-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9002, pid=96
# 2025-03-13T06:41:55,729 [INFO ] W-9006-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9006
# 2025-03-13T06:41:55,729 [INFO ] W-9000-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9000
# 2025-03-13T06:41:55,729 [INFO ] W-9007-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9007
# 2025-03-13T06:41:55,721 [INFO ] W-9012-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9012
# 2025-03-13T06:41:55,729 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9014
# 2025-03-13T06:41:55,729 [INFO ] W-9002-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9002
# 2025-03-13T06:41:55,729 [INFO ] W-9006-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:41:55,717 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9015, pid=98
# 2025-03-13T06:41:55,729 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:41:55,729 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9015
# 2025-03-13T06:41:55,730 [INFO ] W-9006-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - [PID]101
# 2025-03-13T06:41:55,730 [INFO ] W-9001-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9001, pid=93
# 2025-03-13T06:41:55,730 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - [PID]92
# 2025-03-13T06:41:55,730 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:41:55,730 [INFO ] W-9010-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:41:55,724 [INFO ] W-9013-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9013
# 2025-03-13T06:41:55,730 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:41:55,730 [DEBUG] W-9014-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9014-drawn_humanoid_pose_estimator_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:41:55,730 [INFO ] W-9007-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:41:55,729 [INFO ] W-9004-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - [PID]74
# 2025-03-13T06:41:55,730 [INFO ] W-9001-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9001
# 2025-03-13T06:41:55,729 [INFO ] W-9012-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:41:55,717 [INFO ] W-9003-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9003, pid=71
# 2025-03-13T06:41:55,729 [INFO ] W-9011-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9011
# 2025-03-13T06:41:55,732 [DEBUG] W-9006-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9006-drawn_humanoid_pose_estimator_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:41:55,717 [INFO ] W-9005-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9005, pid=99
# 2025-03-13T06:41:55,729 [INFO ] W-9002-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:41:55,729 [INFO ] W-9009-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - [PID]73
# 2025-03-13T06:41:55,732 [INFO ] W-9012-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - [PID]95
# 2025-03-13T06:41:55,732 [INFO ] W-9006-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:41:55,732 [INFO ] W-9001-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:41:55,732 [INFO ] W-9005-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9005
# 2025-03-13T06:41:55,731 [INFO ] W-9010-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - [PID]97
# 2025-03-13T06:41:55,731 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:41:55,731 [INFO ] W-9007-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - [PID]72
# 2025-03-13T06:41:55,731 [INFO ] W-9013-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:41:55,733 [INFO ] W-9009-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:41:55,733 [INFO ] W-9006-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:41:55,732 [INFO ] W-9012-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:41:55,732 [INFO ] W-9003-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9003
# 2025-03-13T06:41:55,733 [INFO ] W-9005-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:41:55,733 [INFO ] W-9007-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:41:55,733 [INFO ] W-9010-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:41:55,733 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - [PID]98
# 2025-03-13T06:41:55,733 [INFO ] W-9004-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:41:55,733 [DEBUG] W-9007-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9007-drawn_humanoid_pose_estimator_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:41:55,733 [INFO ] W-9009-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:41:55,734 [INFO ] W-9004-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:41:55,733 [INFO ] W-9008-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9008, pid=76
# 2025-03-13T06:41:55,733 [INFO ] W-9013-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - [PID]102
# 2025-03-13T06:41:55,733 [INFO ] W-9001-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - [PID]93
# 2025-03-13T06:41:55,733 [DEBUG] W-9012-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9012-drawn_humanoid_pose_estimator_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:41:55,734 [DEBUG] W-9015-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9015-drawn_humanoid_pose_estimator_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:41:55,732 [INFO ] W-9011-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:41:55,734 [INFO ] W-9008-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9008
# 2025-03-13T06:41:55,735 [INFO ] W-9012-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:41:55,735 [INFO ] W-9003-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:41:55,733 [DEBUG] W-9009-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9009-drawn_humanoid_pose_estimator_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:41:55,734 [DEBUG] W-9010-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9010-drawn_humanoid_pose_estimator_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:41:55,734 [INFO ] W-9005-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - [PID]99
# 2025-03-13T06:41:55,735 [INFO ] W-9007-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:41:55,734 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:41:55,734 [INFO ] W-9001-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:41:55,735 [INFO ] W-9003-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - [PID]71
# 2025-03-13T06:41:55,735 [INFO ] W-9005-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:41:55,735 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:41:55,733 [DEBUG] W-9004-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9004-drawn_humanoid_pose_estimator_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:41:55,734 [DEBUG] W-9001-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9001-drawn_humanoid_pose_estimator_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:41:55,735 [INFO ] W-9005-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:41:55,734 [INFO ] W-9013-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:41:55,734 [DEBUG] W-9013-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9013-drawn_humanoid_pose_estimator_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:41:55,735 [DEBUG] W-9005-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9005-drawn_humanoid_pose_estimator_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:41:55,734 [INFO ] W-9002-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - [PID]96
# 2025-03-13T06:41:55,734 [INFO ] W-9010-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:41:55,735 [INFO ] W-9013-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:41:55,735 [DEBUG] W-9003-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9003-drawn_humanoid_pose_estimator_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:41:55,735 [INFO ] W-9003-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:41:55,735 [INFO ] W-9001-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:41:55,736 [INFO ] W-9003-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:41:55,735 [INFO ] W-9011-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - [PID]100
# 2025-03-13T06:41:55,736 [INFO ] W-9002-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:41:55,736 [INFO ] W-9000-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:41:55,736 [DEBUG] W-9002-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9002-drawn_humanoid_pose_estimator_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:41:55,737 [INFO ] W-9002-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:41:55,737 [INFO ] W-9011-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:41:55,737 [DEBUG] W-9011-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9011-drawn_humanoid_pose_estimator_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:41:55,737 [INFO ] W-9000-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - [PID]94
# 2025-03-13T06:41:55,737 [INFO ] W-9011-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:41:55,737 [INFO ] W-9000-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:41:55,737 [DEBUG] W-9000-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9000-drawn_humanoid_pose_estimator_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:41:55,737 [INFO ] W-9000-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:41:55,741 [INFO ] W-9008-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:41:55,742 [INFO ] W-9008-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - [PID]76
# 2025-03-13T06:41:55,742 [INFO ] W-9008-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:41:55,742 [DEBUG] W-9008-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9008-drawn_humanoid_pose_estimator_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:41:55,742 [INFO ] W-9008-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:41:55,745 [INFO ] W-9008-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9008
# 2025-03-13T06:41:55,745 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9015
# 2025-03-13T06:41:55,745 [INFO ] W-9013-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9013
# 2025-03-13T06:41:55,745 [INFO ] W-9004-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9004
# 2025-03-13T06:41:55,745 [INFO ] W-9003-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9003
# 2025-03-13T06:41:55,745 [INFO ] W-9011-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9011
# 2025-03-13T06:41:55,745 [INFO ] W-9002-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9002
# 2025-03-13T06:41:55,745 [INFO ] W-9006-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9006
# 2025-03-13T06:41:55,745 [INFO ] W-9001-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9001
# 2025-03-13T06:41:55,745 [INFO ] W-9007-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9007
# 2025-03-13T06:41:55,745 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9014
# 2025-03-13T06:41:55,745 [INFO ] W-9000-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9000
# 2025-03-13T06:41:55,745 [INFO ] W-9012-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9012
# 2025-03-13T06:41:55,745 [INFO ] W-9005-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9005
# 2025-03-13T06:41:55,745 [INFO ] W-9010-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9010
# 2025-03-13T06:41:55,745 [INFO ] W-9009-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9009
# 2025-03-13T06:41:55,794 [INFO ] W-9003-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9003.
# 2025-03-13T06:41:55,794 [INFO ] W-9007-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9007.
# 2025-03-13T06:41:55,794 [INFO ] W-9004-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9004.
# 2025-03-13T06:41:55,794 [INFO ] W-9006-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9006.
# 2025-03-13T06:41:55,794 [INFO ] W-9009-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9009.
# 2025-03-13T06:41:55,794 [INFO ] W-9002-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9002.
# 2025-03-13T06:41:55,794 [INFO ] W-9008-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9008.
# 2025-03-13T06:41:55,794 [INFO ] W-9001-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9001.
# 2025-03-13T06:41:55,794 [INFO ] W-9010-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9010.
# 2025-03-13T06:41:55,794 [INFO ] W-9013-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9013.
# 2025-03-13T06:41:55,795 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9015.
# 2025-03-13T06:41:55,794 [INFO ] W-9012-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9012.
# 2025-03-13T06:41:55,795 [INFO ] W-9005-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9005.
# 2025-03-13T06:41:55,794 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9014.
# 2025-03-13T06:41:55,794 [INFO ] W-9011-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9011.
# 2025-03-13T06:41:55,795 [INFO ] W-9000-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9000.
# 2025-03-13T06:41:55,799 [DEBUG] W-9013-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848115799
# 2025-03-13T06:41:55,799 [DEBUG] W-9004-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848115799
# 2025-03-13T06:41:55,799 [DEBUG] W-9012-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848115799
# 2025-03-13T06:41:55,799 [DEBUG] W-9001-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848115799
# 2025-03-13T06:41:55,799 [DEBUG] W-9011-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848115799
# 2025-03-13T06:41:55,799 [DEBUG] W-9008-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848115799
# 2025-03-13T06:41:55,799 [DEBUG] W-9006-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848115799
# 2025-03-13T06:41:55,799 [DEBUG] W-9003-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848115799
# 2025-03-13T06:41:55,799 [DEBUG] W-9005-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848115799
# 2025-03-13T06:41:55,799 [DEBUG] W-9009-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848115799
# 2025-03-13T06:41:55,799 [DEBUG] W-9007-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848115799
# 2025-03-13T06:41:55,799 [DEBUG] W-9002-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848115799
# 2025-03-13T06:41:55,799 [DEBUG] W-9014-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848115799
# 2025-03-13T06:41:55,799 [DEBUG] W-9000-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848115799
# 2025-03-13T06:41:55,799 [DEBUG] W-9015-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848115799
# 2025-03-13T06:41:55,799 [DEBUG] W-9010-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848115799
# 2025-03-13T06:41:55,803 [INFO ] W-9011-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848115803
# 2025-03-13T06:41:55,803 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848115803
# 2025-03-13T06:41:55,803 [INFO ] W-9012-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848115803
# 2025-03-13T06:41:55,803 [INFO ] W-9003-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848115803
# 2025-03-13T06:41:55,803 [INFO ] W-9013-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848115803
# 2025-03-13T06:41:55,803 [INFO ] W-9000-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848115803
# 2025-03-13T06:41:55,803 [INFO ] W-9007-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848115803
# 2025-03-13T06:41:55,804 [INFO ] W-9002-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848115803
# 2025-03-13T06:41:55,803 [INFO ] W-9010-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848115803
# 2025-03-13T06:41:55,804 [INFO ] W-9004-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848115804
# 2025-03-13T06:41:55,804 [INFO ] W-9009-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848115804
# 2025-03-13T06:41:55,804 [INFO ] W-9006-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848115804
# 2025-03-13T06:41:55,804 [INFO ] W-9008-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848115804
# 2025-03-13T06:41:55,804 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848115804
# 2025-03-13T06:41:55,804 [INFO ] W-9001-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848115804
# 2025-03-13T06:41:55,804 [INFO ] W-9005-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848115804
# 2025-03-13T06:41:55,861 [INFO ] W-9000-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_pose_estimator, batchSize: 1
# 2025-03-13T06:41:55,862 [INFO ] W-9004-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_pose_estimator, batchSize: 1
# 2025-03-13T06:41:55,862 [INFO ] W-9010-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_pose_estimator, batchSize: 1
# 2025-03-13T06:41:55,861 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_pose_estimator, batchSize: 1
# 2025-03-13T06:41:55,863 [INFO ] W-9001-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_pose_estimator, batchSize: 1
# 2025-03-13T06:41:55,863 [INFO ] W-9013-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_pose_estimator, batchSize: 1
# 2025-03-13T06:41:55,864 [INFO ] W-9008-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_pose_estimator, batchSize: 1
# 2025-03-13T06:41:55,864 [INFO ] W-9009-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_pose_estimator, batchSize: 1
# 2025-03-13T06:41:55,864 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_pose_estimator, batchSize: 1
# 2025-03-13T06:41:55,864 [INFO ] W-9012-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_pose_estimator, batchSize: 1
# 2025-03-13T06:41:55,864 [INFO ] W-9003-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_pose_estimator, batchSize: 1
# 2025-03-13T06:41:55,864 [INFO ] W-9006-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_pose_estimator, batchSize: 1
# 2025-03-13T06:41:55,864 [INFO ] W-9005-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_pose_estimator, batchSize: 1
# 2025-03-13T06:41:55,864 [INFO ] W-9007-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_pose_estimator, batchSize: 1
# 2025-03-13T06:41:55,865 [INFO ] W-9002-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_pose_estimator, batchSize: 1
# 2025-03-13T06:41:55,870 [INFO ] W-9011-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_pose_estimator, batchSize: 1
# 2025-03-13T06:41:58,187 [DEBUG] main org.pytorch.serve.wlm.ModelVersionedRefs - Adding new version 1.0 for model drawn_humanoid_detector
# 2025-03-13T06:41:58,187 [DEBUG] main org.pytorch.serve.wlm.ModelVersionedRefs - Setting default version to 1.0 for model drawn_humanoid_detector
# 2025-03-13T06:41:58,187 [INFO ] main org.pytorch.serve.wlm.ModelManager - Model drawn_humanoid_detector loaded.
# 2025-03-13T06:41:58,188 [DEBUG] main org.pytorch.serve.wlm.ModelManager - updateModel: drawn_humanoid_detector, count: 16
# 2025-03-13T06:41:58,204 [DEBUG] W-9025-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9025, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:58,206 [DEBUG] W-9016-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9016, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:58,206 [DEBUG] W-9022-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9022, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:58,207 [DEBUG] W-9021-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9021, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:58,207 [DEBUG] W-9017-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9017, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:58,206 [DEBUG] W-9018-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9018, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:58,207 [DEBUG] W-9020-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9020, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:58,208 [DEBUG] W-9027-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9027, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:58,210 [DEBUG] W-9029-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9029, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:58,212 [DEBUG] W-9023-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9023, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:58,212 [DEBUG] W-9024-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9024, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:58,212 [DEBUG] W-9019-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9019, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:58,213 [DEBUG] W-9030-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9030, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:58,218 [INFO ] main org.pytorch.serve.ModelServer - Initialize Inference server with: EpollServerSocketChannel.
# 2025-03-13T06:41:58,206 [DEBUG] W-9026-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9026, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:58,210 [DEBUG] W-9028-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9028, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:58,223 [DEBUG] W-9031-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerLifeCycle - Worker cmdline: [/opt/conda/bin/python, /opt/conda/lib/python3.8/site-packages/ts/model_service_worker.py, --sock-type, unix, --sock-name, /tmp/.ts.sock.9031, --metrics-config, /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml]
# 2025-03-13T06:41:58,348 [INFO ] main org.pytorch.serve.ModelServer - Inference API bind to: http://0.0.0.0:8080
# 2025-03-13T06:41:58,348 [INFO ] main org.pytorch.serve.ModelServer - Initialize Management server with: EpollServerSocketChannel.
# 2025-03-13T06:41:58,365 [INFO ] main org.pytorch.serve.ModelServer - Management API bind to: http://0.0.0.0:8081
# 2025-03-13T06:41:58,366 [INFO ] main org.pytorch.serve.ModelServer - Initialize Metrics server with: EpollServerSocketChannel.
# 2025-03-13T06:41:58,367 [INFO ] main org.pytorch.serve.ModelServer - Metrics API bind to: http://0.0.0.0:8082
# Model server started.
# 2025-03-13T06:41:59,305 [WARN ] pool-3-thread-1 org.pytorch.serve.metrics.MetricCollector - worker pid is not available yet.
# 2025-03-13T06:41:59,483 [INFO ] pool-3-thread-1 TS_METRICS - CPUUtilization.Percent:100.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848119
# 2025-03-13T06:41:59,486 [INFO ] pool-3-thread-1 TS_METRICS - DiskAvailable.Gigabytes:278.98888778686523|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848119
# 2025-03-13T06:41:59,486 [INFO ] pool-3-thread-1 TS_METRICS - DiskUsage.Gigabytes:164.1733627319336|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848119
# 2025-03-13T06:41:59,486 [INFO ] pool-3-thread-1 TS_METRICS - DiskUtilization.Percent:37.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848119
# 2025-03-13T06:41:59,486 [INFO ] pool-3-thread-1 TS_METRICS - MemoryAvailable.Megabytes:51764.7109375|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848119
# 2025-03-13T06:41:59,486 [INFO ] pool-3-thread-1 TS_METRICS - MemoryUsed.Megabytes:7735.55078125|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848119
# 2025-03-13T06:41:59,486 [INFO ] pool-3-thread-1 TS_METRICS - MemoryUtilization.Percent:13.9|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848119
# 2025-03-13T06:42:00,171 [INFO ] W-9000-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:00,173 [INFO ] W-9002-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:00,173 [INFO ] W-9002-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:00,173 [INFO ] W-9002-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:00,177 [INFO ] W-9013-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:00,177 [INFO ] W-9013-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:00,177 [INFO ] W-9013-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:00,177 [INFO ] W-9007-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:00,178 [INFO ] W-9007-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:00,178 [INFO ] W-9007-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:00,181 [INFO ] W-9005-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:00,181 [INFO ] W-9000-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:00,181 [INFO ] W-9003-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:00,181 [INFO ] W-9003-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:00,182 [INFO ] W-9003-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:00,181 [INFO ] W-9005-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:00,182 [INFO ] W-9005-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:00,185 [INFO ] W-9000-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:00,193 [INFO ] W-9006-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:00,193 [INFO ] W-9006-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:00,193 [INFO ] W-9006-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:00,195 [INFO ] W-9004-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:00,195 [INFO ] W-9004-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:00,196 [INFO ] W-9004-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:00,197 [INFO ] W-9010-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:00,197 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:00,197 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:00,197 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:00,205 [INFO ] W-9010-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:00,205 [INFO ] W-9010-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:00,224 [INFO ] W-9011-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:00,229 [INFO ] W-9011-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:00,229 [INFO ] W-9011-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:00,232 [INFO ] W-9008-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:00,232 [INFO ] W-9008-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:00,234 [INFO ] W-9008-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:00,253 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:00,253 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:00,254 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:00,353 [INFO ] W-9012-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:00,353 [INFO ] W-9012-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:00,353 [INFO ] W-9012-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:00,729 [INFO ] W-9001-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:00,729 [INFO ] W-9001-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:00,730 [INFO ] W-9001-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:00,825 [INFO ] W-9009-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:00,825 [INFO ] W-9009-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:00,826 [INFO ] W-9009-drawn_humanoid_pose_estimator_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:01,341 [INFO ] W-9017-drawn_humanoid_detector_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9017, pid=784
# 2025-03-13T06:42:01,342 [INFO ] W-9017-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9017
# 2025-03-13T06:42:01,358 [INFO ] W-9017-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:42:01,361 [INFO ] W-9017-drawn_humanoid_detector_1.0-stdout MODEL_LOG - [PID]784
# 2025-03-13T06:42:01,365 [INFO ] W-9017-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:42:01,366 [INFO ] W-9017-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:42:01,365 [DEBUG] W-9017-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9017-drawn_humanoid_detector_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:42:01,366 [INFO ] W-9017-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9017
# 2025-03-13T06:42:01,396 [DEBUG] W-9017-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848121396
# 2025-03-13T06:42:01,396 [INFO ] W-9017-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848121396
# 2025-03-13T06:42:01,397 [INFO ] W-9017-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9017.
# 2025-03-13T06:42:01,421 [INFO ] W-9017-drawn_humanoid_detector_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_detector, batchSize: 1
# 2025-03-13T06:42:01,755 [INFO ] W-9020-drawn_humanoid_detector_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9020, pid=786
# 2025-03-13T06:42:01,755 [INFO ] W-9020-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9020
# 2025-03-13T06:42:01,790 [INFO ] W-9020-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:42:01,791 [INFO ] W-9020-drawn_humanoid_detector_1.0-stdout MODEL_LOG - [PID]786
# 2025-03-13T06:42:01,791 [INFO ] W-9020-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:42:01,791 [INFO ] W-9020-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:42:01,791 [DEBUG] W-9020-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9020-drawn_humanoid_detector_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:42:01,791 [INFO ] W-9020-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9020
# 2025-03-13T06:42:01,802 [DEBUG] W-9020-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848121802
# 2025-03-13T06:42:01,802 [INFO ] W-9020-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848121802
# 2025-03-13T06:42:01,803 [INFO ] W-9020-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9020.
# 2025-03-13T06:42:01,821 [INFO ] W-9020-drawn_humanoid_detector_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_detector, batchSize: 1
# 2025-03-13T06:42:01,833 [INFO ] W-9018-drawn_humanoid_detector_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9018, pid=785
# 2025-03-13T06:42:01,850 [INFO ] W-9018-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9018
# 2025-03-13T06:42:01,870 [INFO ] W-9018-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:42:01,870 [INFO ] W-9018-drawn_humanoid_detector_1.0-stdout MODEL_LOG - [PID]785
# 2025-03-13T06:42:01,871 [DEBUG] W-9018-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9018-drawn_humanoid_detector_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:42:01,871 [INFO ] W-9018-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9018
# 2025-03-13T06:42:01,872 [INFO ] W-9018-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:42:01,872 [INFO ] W-9018-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:42:01,903 [INFO ] W-9018-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9018.
# 2025-03-13T06:42:01,903 [DEBUG] W-9018-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848121903
# 2025-03-13T06:42:01,903 [INFO ] W-9018-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848121903
# 2025-03-13T06:42:01,945 [INFO ] W-9018-drawn_humanoid_detector_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_detector, batchSize: 1
# 2025-03-13T06:42:02,040 [INFO ] W-9023-drawn_humanoid_detector_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9023, pid=789
# 2025-03-13T06:42:02,061 [INFO ] W-9023-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9023
# 2025-03-13T06:42:02,089 [INFO ] W-9023-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:42:02,112 [INFO ] W-9023-drawn_humanoid_detector_1.0-stdout MODEL_LOG - [PID]789
# 2025-03-13T06:42:02,112 [INFO ] W-9023-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:42:02,112 [INFO ] W-9023-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:42:02,112 [DEBUG] W-9023-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9023-drawn_humanoid_detector_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:42:02,113 [INFO ] W-9023-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9023
# 2025-03-13T06:42:02,122 [INFO ] W-9025-drawn_humanoid_detector_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9025, pid=777
# 2025-03-13T06:42:02,125 [DEBUG] W-9023-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848122125
# 2025-03-13T06:42:02,126 [INFO ] W-9023-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848122126
# 2025-03-13T06:42:02,126 [INFO ] W-9023-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9023.
# 2025-03-13T06:42:02,133 [INFO ] W-9025-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9025
# 2025-03-13T06:42:02,143 [INFO ] W-9023-drawn_humanoid_detector_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_detector, batchSize: 1
# 2025-03-13T06:42:02,170 [INFO ] W-9025-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:42:02,171 [INFO ] W-9025-drawn_humanoid_detector_1.0-stdout MODEL_LOG - [PID]777
# 2025-03-13T06:42:02,171 [INFO ] W-9025-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:42:02,171 [INFO ] W-9025-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:42:02,171 [DEBUG] W-9025-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9025-drawn_humanoid_detector_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:42:02,172 [INFO ] W-9025-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9025
# 2025-03-13T06:42:02,175 [INFO ] W-9025-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9025.
# 2025-03-13T06:42:02,175 [DEBUG] W-9025-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848122175
# 2025-03-13T06:42:02,176 [INFO ] W-9025-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848122175
# 2025-03-13T06:42:02,210 [INFO ] W-9025-drawn_humanoid_detector_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_detector, batchSize: 1
# 2025-03-13T06:42:02,592 [INFO ] W-9029-drawn_humanoid_detector_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9029, pid=788
# 2025-03-13T06:42:02,593 [INFO ] W-9029-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9029
# 2025-03-13T06:42:02,620 [INFO ] W-9028-drawn_humanoid_detector_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9028, pid=801
# 2025-03-13T06:42:02,649 [INFO ] W-9028-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9028
# 2025-03-13T06:42:02,729 [INFO ] W-9029-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:42:02,750 [INFO ] W-9028-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:42:02,757 [INFO ] W-9029-drawn_humanoid_detector_1.0-stdout MODEL_LOG - [PID]788
# 2025-03-13T06:42:02,757 [INFO ] W-9029-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:42:02,757 [INFO ] W-9029-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:42:02,757 [INFO ] W-9028-drawn_humanoid_detector_1.0-stdout MODEL_LOG - [PID]801
# 2025-03-13T06:42:02,758 [INFO ] W-9028-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:42:02,758 [INFO ] W-9028-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:42:02,757 [DEBUG] W-9029-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9029-drawn_humanoid_detector_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:42:02,758 [INFO ] W-9029-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9029
# 2025-03-13T06:42:02,759 [DEBUG] W-9028-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9028-drawn_humanoid_detector_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:42:02,759 [INFO ] W-9028-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9028
# 2025-03-13T06:42:02,786 [INFO ] W-9028-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9028.
# 2025-03-13T06:42:02,786 [DEBUG] W-9028-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848122786
# 2025-03-13T06:42:02,786 [INFO ] W-9028-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848122786
# 2025-03-13T06:42:02,805 [INFO ] W-9028-drawn_humanoid_detector_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_detector, batchSize: 1
# 2025-03-13T06:42:02,805 [INFO ] W-9029-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9029.
# 2025-03-13T06:42:02,806 [DEBUG] W-9029-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848122806
# 2025-03-13T06:42:02,806 [INFO ] W-9029-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848122806
# 2025-03-13T06:42:02,998 [INFO ] W-9021-drawn_humanoid_detector_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9021, pid=783
# 2025-03-13T06:42:02,999 [INFO ] W-9021-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9021
# 2025-03-13T06:42:03,009 [INFO ] W-9029-drawn_humanoid_detector_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_detector, batchSize: 1
# 2025-03-13T06:42:03,102 [INFO ] W-9021-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:42:03,132 [INFO ] W-9021-drawn_humanoid_detector_1.0-stdout MODEL_LOG - [PID]783
# 2025-03-13T06:42:03,133 [INFO ] W-9021-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:42:03,137 [INFO ] W-9021-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:42:03,137 [DEBUG] W-9021-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9021-drawn_humanoid_detector_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:42:03,138 [INFO ] W-9021-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9021
# 2025-03-13T06:42:03,166 [DEBUG] W-9021-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848123166
# 2025-03-13T06:42:03,173 [INFO ] W-9021-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848123173
# 2025-03-13T06:42:03,174 [INFO ] W-9021-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9021.
# 2025-03-13T06:42:03,274 [INFO ] W-9021-drawn_humanoid_detector_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_detector, batchSize: 1
# 2025-03-13T06:42:03,353 [INFO ] W-9026-drawn_humanoid_detector_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9026, pid=797
# 2025-03-13T06:42:03,354 [INFO ] W-9026-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9026
# 2025-03-13T06:42:03,354 [INFO ] W-9020-drawn_humanoid_detector_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:03,355 [INFO ] W-9020-drawn_humanoid_detector_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:03,355 [INFO ] W-9020-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:03,370 [INFO ] W-9026-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:42:03,425 [INFO ] W-9026-drawn_humanoid_detector_1.0-stdout MODEL_LOG - [PID]797
# 2025-03-13T06:42:03,426 [DEBUG] W-9026-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9026-drawn_humanoid_detector_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:42:03,426 [INFO ] W-9026-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9026
# 2025-03-13T06:42:03,427 [INFO ] W-9026-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:42:03,427 [INFO ] W-9026-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:42:03,442 [DEBUG] W-9026-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848123442
# 2025-03-13T06:42:03,442 [INFO ] W-9026-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848123442
# 2025-03-13T06:42:03,444 [INFO ] W-9026-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9026.
# 2025-03-13T06:42:03,627 [INFO ] W-9024-drawn_humanoid_detector_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9024, pid=791
# 2025-03-13T06:42:03,627 [INFO ] W-9024-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9024
# 2025-03-13T06:42:03,632 [INFO ] W-9026-drawn_humanoid_detector_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_detector, batchSize: 1
# 2025-03-13T06:42:03,634 [INFO ] W-9024-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:42:03,648 [INFO ] W-9024-drawn_humanoid_detector_1.0-stdout MODEL_LOG - [PID]791
# 2025-03-13T06:42:03,648 [INFO ] W-9024-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:42:03,648 [INFO ] W-9024-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:42:03,656 [DEBUG] W-9024-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9024-drawn_humanoid_detector_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:42:03,657 [INFO ] W-9024-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9024
# 2025-03-13T06:42:03,829 [DEBUG] W-9024-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848123829
# 2025-03-13T06:42:03,830 [INFO ] W-9024-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848123830
# 2025-03-13T06:42:03,841 [INFO ] W-9024-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9024.
# 2025-03-13T06:42:03,901 [INFO ] W-9025-drawn_humanoid_detector_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:03,901 [INFO ] W-9024-drawn_humanoid_detector_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_detector, batchSize: 1
# 2025-03-13T06:42:03,901 [INFO ] W-9025-drawn_humanoid_detector_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:03,901 [INFO ] W-9025-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:03,909 [INFO ] W-9011-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 8106
# 2025-03-13T06:42:03,909 [DEBUG] W-9011-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9011-drawn_humanoid_pose_estimator_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:03,910 [INFO ] W-9011-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:10599.0|#WorkerName:W-9011-drawn_humanoid_pose_estimator_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848123
# 2025-03-13T06:42:03,913 [INFO ] W-9011-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:8.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848123
# 2025-03-13T06:42:03,937 [INFO ] W-9030-drawn_humanoid_detector_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9030, pid=793
# 2025-03-13T06:42:03,941 [INFO ] W-9030-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9030
# 2025-03-13T06:42:03,950 [INFO ] W-9030-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:42:03,950 [INFO ] W-9030-drawn_humanoid_detector_1.0-stdout MODEL_LOG - [PID]793
# 2025-03-13T06:42:03,951 [INFO ] W-9030-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:42:03,951 [INFO ] W-9030-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:42:03,951 [DEBUG] W-9030-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9030-drawn_humanoid_detector_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:42:03,951 [INFO ] W-9030-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9030
# 2025-03-13T06:42:03,957 [DEBUG] W-9030-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848123957
# 2025-03-13T06:42:03,958 [INFO ] W-9030-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848123958
# 2025-03-13T06:42:03,958 [INFO ] W-9030-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9030.
# 2025-03-13T06:42:04,018 [INFO ] W-9030-drawn_humanoid_detector_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_detector, batchSize: 1
# 2025-03-13T06:42:04,105 [INFO ] W-9027-drawn_humanoid_detector_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9027, pid=787
# 2025-03-13T06:42:04,106 [INFO ] W-9027-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9027
# 2025-03-13T06:42:04,128 [INFO ] W-9027-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:42:04,130 [INFO ] W-9027-drawn_humanoid_detector_1.0-stdout MODEL_LOG - [PID]787
# 2025-03-13T06:42:04,130 [INFO ] W-9027-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:42:04,130 [INFO ] W-9027-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:42:04,130 [DEBUG] W-9027-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9027-drawn_humanoid_detector_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:42:04,130 [INFO ] W-9027-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9027
# 2025-03-13T06:42:04,151 [DEBUG] W-9027-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848124151
# 2025-03-13T06:42:04,151 [INFO ] W-9016-drawn_humanoid_detector_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9016, pid=781
# 2025-03-13T06:42:04,151 [INFO ] W-9027-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848124151
# 2025-03-13T06:42:04,151 [INFO ] W-9016-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9016
# 2025-03-13T06:42:04,152 [INFO ] W-9027-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9027.
# 2025-03-13T06:42:04,205 [INFO ] W-9027-drawn_humanoid_detector_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_detector, batchSize: 1
# 2025-03-13T06:42:04,295 [INFO ] W-9016-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:42:04,295 [INFO ] W-9016-drawn_humanoid_detector_1.0-stdout MODEL_LOG - [PID]781
# 2025-03-13T06:42:04,295 [INFO ] W-9016-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:42:04,295 [INFO ] W-9016-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:42:04,310 [DEBUG] W-9016-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9016-drawn_humanoid_detector_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:42:04,311 [INFO ] W-9016-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9016
# 2025-03-13T06:42:04,338 [DEBUG] W-9016-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848124338
# 2025-03-13T06:42:04,339 [INFO ] W-9016-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848124339
# 2025-03-13T06:42:04,401 [INFO ] W-9016-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9016.
# 2025-03-13T06:42:04,437 [INFO ] W-9016-drawn_humanoid_detector_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_detector, batchSize: 1
# 2025-03-13T06:42:04,539 [INFO ] W-9023-drawn_humanoid_detector_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:04,539 [INFO ] W-9023-drawn_humanoid_detector_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:04,541 [INFO ] W-9023-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:04,757 [INFO ] W-9017-drawn_humanoid_detector_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:04,758 [INFO ] W-9017-drawn_humanoid_detector_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:04,758 [INFO ] W-9017-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:04,945 [INFO ] W-9022-drawn_humanoid_detector_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9022, pid=782
# 2025-03-13T06:42:04,945 [INFO ] W-9022-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9022
# 2025-03-13T06:42:04,957 [INFO ] W-9022-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:42:04,969 [INFO ] W-9022-drawn_humanoid_detector_1.0-stdout MODEL_LOG - [PID]782
# 2025-03-13T06:42:04,970 [INFO ] W-9022-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:42:04,970 [INFO ] W-9022-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:42:04,970 [DEBUG] W-9022-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9022-drawn_humanoid_detector_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:42:04,970 [INFO ] W-9022-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9022
# 2025-03-13T06:42:04,986 [DEBUG] W-9022-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848124986
# 2025-03-13T06:42:04,987 [INFO ] W-9022-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848124987
# 2025-03-13T06:42:05,017 [INFO ] W-9022-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9022.
# 2025-03-13T06:42:05,018 [INFO ] W-9005-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 9213
# 2025-03-13T06:42:05,018 [DEBUG] W-9005-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9005-drawn_humanoid_pose_estimator_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:05,018 [INFO ] W-9005-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:11708.0|#WorkerName:W-9005-drawn_humanoid_pose_estimator_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848125
# 2025-03-13T06:42:05,018 [INFO ] W-9005-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:6.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848125
# 2025-03-13T06:42:05,024 [INFO ] W-9022-drawn_humanoid_detector_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_detector, batchSize: 1
# 2025-03-13T06:42:05,367 [INFO ] W-9031-drawn_humanoid_detector_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9031, pid=802
# 2025-03-13T06:42:05,367 [INFO ] W-9031-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9031
# 2025-03-13T06:42:05,367 [INFO ] W-9018-drawn_humanoid_detector_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:05,368 [INFO ] W-9018-drawn_humanoid_detector_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:05,368 [INFO ] W-9018-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:05,393 [INFO ] W-9031-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:42:05,394 [INFO ] W-9031-drawn_humanoid_detector_1.0-stdout MODEL_LOG - [PID]802
# 2025-03-13T06:42:05,394 [INFO ] W-9031-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:42:05,394 [INFO ] W-9031-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:42:05,394 [DEBUG] W-9031-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9031-drawn_humanoid_detector_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:42:05,395 [INFO ] W-9031-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9031
# 2025-03-13T06:42:05,398 [DEBUG] W-9031-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848125398
# 2025-03-13T06:42:05,398 [INFO ] W-9031-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848125398
# 2025-03-13T06:42:05,457 [INFO ] W-9019-drawn_humanoid_detector_1.0-stdout MODEL_LOG - s_name_part0=/tmp/.ts.sock, s_name_part1=9019, pid=792
# 2025-03-13T06:42:05,457 [INFO ] W-9019-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Listening on port: /tmp/.ts.sock.9019
# 2025-03-13T06:42:05,460 [INFO ] W-9030-drawn_humanoid_detector_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:05,460 [INFO ] W-9030-drawn_humanoid_detector_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:05,460 [INFO ] W-9030-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:05,460 [INFO ] W-9031-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9031.
# 2025-03-13T06:42:05,469 [INFO ] W-9019-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Successfully loaded /opt/conda/lib/python3.8/site-packages/ts/configs/metrics.yaml.
# 2025-03-13T06:42:05,475 [INFO ] W-9027-drawn_humanoid_detector_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:05,475 [INFO ] W-9027-drawn_humanoid_detector_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:05,475 [INFO ] W-9027-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:05,478 [INFO ] W-9019-drawn_humanoid_detector_1.0-stdout MODEL_LOG - [PID]792
# 2025-03-13T06:42:05,478 [INFO ] W-9019-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch worker started.
# 2025-03-13T06:42:05,478 [DEBUG] W-9019-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9019-drawn_humanoid_detector_1.0 State change null -> WORKER_STARTED
# 2025-03-13T06:42:05,478 [INFO ] W-9019-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Connecting to: /tmp/.ts.sock.9019
# 2025-03-13T06:42:05,478 [INFO ] W-9019-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Python runtime: 3.8.13
# 2025-03-13T06:42:05,478 [INFO ] W-9031-drawn_humanoid_detector_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_detector, batchSize: 1
# 2025-03-13T06:42:05,502 [INFO ] W-9019-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Connection accepted: /tmp/.ts.sock.9019.
# 2025-03-13T06:42:05,503 [DEBUG] W-9019-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Flushing req.cmd LOAD repeats 1 to backend at: 1741848125503
# 2025-03-13T06:42:05,503 [INFO ] W-9019-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Looping backend response at: 1741848125503
# 2025-03-13T06:42:05,517 [INFO ] W-9019-drawn_humanoid_detector_1.0-stdout MODEL_LOG - model_name: drawn_humanoid_detector, batchSize: 1
# 2025-03-13T06:42:05,546 [INFO ] W-9010-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 9742
# 2025-03-13T06:42:05,546 [DEBUG] W-9010-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9010-drawn_humanoid_pose_estimator_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:05,546 [INFO ] W-9010-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:12235.0|#WorkerName:W-9010-drawn_humanoid_pose_estimator_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848125
# 2025-03-13T06:42:05,549 [INFO ] W-9010-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:8.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848125
# 2025-03-13T06:42:05,597 [INFO ] W-9016-drawn_humanoid_detector_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:05,597 [INFO ] W-9016-drawn_humanoid_detector_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:05,597 [INFO ] W-9016-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:05,708 [INFO ] W-9029-drawn_humanoid_detector_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:05,714 [INFO ] W-9029-drawn_humanoid_detector_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:05,738 [INFO ] W-9029-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:05,866 [INFO ] W-9004-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 10062
# 2025-03-13T06:42:05,866 [DEBUG] W-9004-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9004-drawn_humanoid_pose_estimator_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:05,866 [INFO ] W-9004-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:12556.0|#WorkerName:W-9004-drawn_humanoid_pose_estimator_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848125
# 2025-03-13T06:42:05,867 [INFO ] W-9004-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:6.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848125
# 2025-03-13T06:42:06,069 [INFO ] W-9013-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 10266
# 2025-03-13T06:42:06,069 [DEBUG] W-9013-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9013-drawn_humanoid_pose_estimator_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:06,070 [INFO ] W-9013-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:12757.0|#WorkerName:W-9013-drawn_humanoid_pose_estimator_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848126
# 2025-03-13T06:42:06,070 [INFO ] W-9013-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:5.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848126
# 2025-03-13T06:42:06,224 [INFO ] W-9022-drawn_humanoid_detector_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:06,225 [INFO ] W-9022-drawn_humanoid_detector_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:06,225 [INFO ] W-9022-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:06,317 [INFO ] W-9026-drawn_humanoid_detector_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:06,317 [INFO ] W-9026-drawn_humanoid_detector_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:06,320 [INFO ] W-9026-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:06,481 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 10678
# 2025-03-13T06:42:06,481 [DEBUG] W-9015-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9015-drawn_humanoid_pose_estimator_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:06,482 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:13170.0|#WorkerName:W-9015-drawn_humanoid_pose_estimator_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848126
# 2025-03-13T06:42:06,482 [INFO ] W-9015-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:5.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848126
# 2025-03-13T06:42:06,524 [INFO ] W-9001-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 10720
# 2025-03-13T06:42:06,524 [DEBUG] W-9001-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9001-drawn_humanoid_pose_estimator_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:06,525 [INFO ] W-9001-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:13215.0|#WorkerName:W-9001-drawn_humanoid_pose_estimator_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848126
# 2025-03-13T06:42:06,525 [INFO ] W-9001-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:6.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848126
# 2025-03-13T06:42:06,580 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 10776
# 2025-03-13T06:42:06,581 [DEBUG] W-9014-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9014-drawn_humanoid_pose_estimator_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:06,585 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:13273.0|#WorkerName:W-9014-drawn_humanoid_pose_estimator_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848126
# 2025-03-13T06:42:06,586 [INFO ] W-9014-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:11.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848126
# 2025-03-13T06:42:06,900 [INFO ] W-9028-drawn_humanoid_detector_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:06,908 [INFO ] W-9028-drawn_humanoid_detector_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:06,908 [INFO ] W-9028-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:06,925 [INFO ] W-9009-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 11121
# 2025-03-13T06:42:06,926 [DEBUG] W-9009-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9009-drawn_humanoid_pose_estimator_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:06,926 [INFO ] W-9009-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:13615.0|#WorkerName:W-9009-drawn_humanoid_pose_estimator_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848126
# 2025-03-13T06:42:06,926 [INFO ] W-9009-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:6.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848126
# 2025-03-13T06:42:06,993 [INFO ] W-9019-drawn_humanoid_detector_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:06,994 [INFO ] W-9019-drawn_humanoid_detector_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:06,994 [INFO ] W-9019-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:07,102 [INFO ] W-9007-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 11299
# 2025-03-13T06:42:07,102 [DEBUG] W-9007-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9007-drawn_humanoid_pose_estimator_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:07,102 [INFO ] W-9007-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:13791.0|#WorkerName:W-9007-drawn_humanoid_pose_estimator_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848127
# 2025-03-13T06:42:07,103 [INFO ] W-9007-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:5.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848127
# 2025-03-13T06:42:07,497 [INFO ] W-9006-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 11693
# 2025-03-13T06:42:07,497 [DEBUG] W-9006-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9006-drawn_humanoid_pose_estimator_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:07,497 [INFO ] W-9006-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:14187.0|#WorkerName:W-9006-drawn_humanoid_pose_estimator_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848127
# 2025-03-13T06:42:07,498 [INFO ] W-9006-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:6.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848127
# 2025-03-13T06:42:07,604 [INFO ] W-9024-drawn_humanoid_detector_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:07,605 [INFO ] W-9024-drawn_humanoid_detector_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:07,605 [INFO ] W-9024-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:07,982 [INFO ] W-9021-drawn_humanoid_detector_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:07,982 [INFO ] W-9021-drawn_humanoid_detector_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:07,982 [INFO ] W-9021-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:07,987 [INFO ] W-9000-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 12184
# 2025-03-13T06:42:07,987 [DEBUG] W-9000-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9000-drawn_humanoid_pose_estimator_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:07,987 [INFO ] W-9000-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:14679.0|#WorkerName:W-9000-drawn_humanoid_pose_estimator_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848127
# 2025-03-13T06:42:07,988 [INFO ] W-9000-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:5.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848127
# 2025-03-13T06:42:08,021 [INFO ] W-9002-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 12217
# 2025-03-13T06:42:08,022 [DEBUG] W-9002-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9002-drawn_humanoid_pose_estimator_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:08,022 [INFO ] W-9002-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:14713.0|#WorkerName:W-9002-drawn_humanoid_pose_estimator_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848128
# 2025-03-13T06:42:08,023 [INFO ] W-9002-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:6.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848128
# 2025-03-13T06:42:08,037 [INFO ] W-9003-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 12234
# 2025-03-13T06:42:08,037 [DEBUG] W-9003-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9003-drawn_humanoid_pose_estimator_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:08,037 [INFO ] W-9003-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:14727.0|#WorkerName:W-9003-drawn_humanoid_pose_estimator_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848128
# 2025-03-13T06:42:08,038 [INFO ] W-9003-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:5.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848128
# 2025-03-13T06:42:08,045 [INFO ] W-9008-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 12241
# 2025-03-13T06:42:08,045 [DEBUG] W-9008-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9008-drawn_humanoid_pose_estimator_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:08,051 [INFO ] W-9008-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:14734.0|#WorkerName:W-9008-drawn_humanoid_pose_estimator_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848128
# 2025-03-13T06:42:08,051 [INFO ] W-9008-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:11.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848128
# 2025-03-13T06:42:08,054 [INFO ] W-9012-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 12251
# 2025-03-13T06:42:08,054 [DEBUG] W-9012-drawn_humanoid_pose_estimator_1.0 org.pytorch.serve.wlm.WorkerThread - W-9012-drawn_humanoid_pose_estimator_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:08,057 [INFO ] W-9012-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:14745.0|#WorkerName:W-9012-drawn_humanoid_pose_estimator_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848128
# 2025-03-13T06:42:08,057 [INFO ] W-9012-drawn_humanoid_pose_estimator_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:7.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848128
# 2025-03-13T06:42:08,131 [INFO ] W-9031-drawn_humanoid_detector_1.0-stdout MODEL_LOG - OpenVINO is not enabled
# 2025-03-13T06:42:08,141 [INFO ] W-9031-drawn_humanoid_detector_1.0-stdout MODEL_LOG - proceeding without onnxruntime
# 2025-03-13T06:42:08,141 [INFO ] W-9031-drawn_humanoid_detector_1.0-stdout MODEL_LOG - Torch TensorRT not enabled
# 2025-03-13T06:42:10,585 [INFO ] W-9020-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 8783
# 2025-03-13T06:42:10,585 [DEBUG] W-9020-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9020-drawn_humanoid_detector_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:10,586 [INFO ] W-9020-drawn_humanoid_detector_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:12391.0|#WorkerName:W-9020-drawn_humanoid_detector_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848130
# 2025-03-13T06:42:10,586 [INFO ] W-9020-drawn_humanoid_detector_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:1.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848130
# 2025-03-13T06:42:10,725 [INFO ] W-9030-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 6767
# 2025-03-13T06:42:10,725 [DEBUG] W-9030-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9030-drawn_humanoid_detector_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:10,726 [INFO ] W-9030-drawn_humanoid_detector_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:12520.0|#WorkerName:W-9030-drawn_humanoid_detector_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848130
# 2025-03-13T06:42:10,726 [INFO ] W-9030-drawn_humanoid_detector_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:2.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848130
# 2025-03-13T06:42:11,163 [INFO ] W-9023-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 9037
# 2025-03-13T06:42:11,164 [DEBUG] W-9023-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9023-drawn_humanoid_detector_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:11,164 [INFO ] W-9023-drawn_humanoid_detector_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:12970.0|#WorkerName:W-9023-drawn_humanoid_detector_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848131
# 2025-03-13T06:42:11,164 [INFO ] W-9023-drawn_humanoid_detector_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:2.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848131
# 2025-03-13T06:42:11,457 [INFO ] W-9025-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 9281
# 2025-03-13T06:42:11,457 [DEBUG] W-9025-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9025-drawn_humanoid_detector_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:11,457 [INFO ] W-9025-drawn_humanoid_detector_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:13260.0|#WorkerName:W-9025-drawn_humanoid_detector_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848131
# 2025-03-13T06:42:11,457 [INFO ] W-9025-drawn_humanoid_detector_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:1.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848131
# 2025-03-13T06:42:11,461 [INFO ] W-9022-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 6474
# 2025-03-13T06:42:11,461 [DEBUG] W-9022-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9022-drawn_humanoid_detector_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:11,461 [INFO ] W-9022-drawn_humanoid_detector_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:13267.0|#WorkerName:W-9022-drawn_humanoid_detector_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848131
# 2025-03-13T06:42:11,461 [INFO ] W-9022-drawn_humanoid_detector_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:1.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848131
# 2025-03-13T06:42:11,597 [INFO ] W-9018-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 9694
# 2025-03-13T06:42:11,597 [DEBUG] W-9018-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9018-drawn_humanoid_detector_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:11,597 [INFO ] W-9018-drawn_humanoid_detector_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:13404.0|#WorkerName:W-9018-drawn_humanoid_detector_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848131
# 2025-03-13T06:42:11,597 [INFO ] W-9018-drawn_humanoid_detector_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:0.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848131
# 2025-03-13T06:42:11,882 [INFO ] W-9028-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 9095
# 2025-03-13T06:42:11,882 [DEBUG] W-9028-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9028-drawn_humanoid_detector_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:11,882 [INFO ] W-9028-drawn_humanoid_detector_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:13677.0|#WorkerName:W-9028-drawn_humanoid_detector_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848131
# 2025-03-13T06:42:11,883 [INFO ] W-9028-drawn_humanoid_detector_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:1.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848131
# 2025-03-13T06:42:12,021 [INFO ] W-9019-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 6518
# 2025-03-13T06:42:12,021 [DEBUG] W-9019-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9019-drawn_humanoid_detector_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:12,021 [INFO ] W-9019-drawn_humanoid_detector_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:13828.0|#WorkerName:W-9019-drawn_humanoid_detector_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848132
# 2025-03-13T06:42:12,021 [INFO ] W-9019-drawn_humanoid_detector_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:0.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848132
# 2025-03-13T06:42:12,139 [INFO ] W-9027-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 7988
# 2025-03-13T06:42:12,139 [DEBUG] W-9027-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9027-drawn_humanoid_detector_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:12,139 [INFO ] W-9027-drawn_humanoid_detector_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:13934.0|#WorkerName:W-9027-drawn_humanoid_detector_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848132
# 2025-03-13T06:42:12,139 [INFO ] W-9027-drawn_humanoid_detector_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:0.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848132
# 2025-03-13T06:42:12,470 [INFO ] W-9017-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 11074
# 2025-03-13T06:42:12,470 [DEBUG] W-9017-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9017-drawn_humanoid_detector_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:12,470 [INFO ] W-9017-drawn_humanoid_detector_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:14277.0|#WorkerName:W-9017-drawn_humanoid_detector_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848132
# 2025-03-13T06:42:12,470 [INFO ] W-9017-drawn_humanoid_detector_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:0.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848132
# 2025-03-13T06:42:12,689 [INFO ] W-9031-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 7291
# 2025-03-13T06:42:12,689 [DEBUG] W-9031-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9031-drawn_humanoid_detector_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:12,689 [INFO ] W-9031-drawn_humanoid_detector_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:14477.0|#WorkerName:W-9031-drawn_humanoid_detector_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848132
# 2025-03-13T06:42:12,689 [INFO ] W-9031-drawn_humanoid_detector_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:0.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848132
# 2025-03-13T06:42:12,857 [INFO ] W-9016-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 8456
# 2025-03-13T06:42:12,857 [DEBUG] W-9016-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9016-drawn_humanoid_detector_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:12,857 [INFO ] W-9016-drawn_humanoid_detector_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:14668.0|#WorkerName:W-9016-drawn_humanoid_detector_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848132
# 2025-03-13T06:42:12,857 [INFO ] W-9016-drawn_humanoid_detector_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:63.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848132
# 2025-03-13T06:42:12,859 [INFO ] W-9029-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 10053
# 2025-03-13T06:42:12,859 [DEBUG] W-9029-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9029-drawn_humanoid_detector_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:12,859 [INFO ] W-9029-drawn_humanoid_detector_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:14654.0|#WorkerName:W-9029-drawn_humanoid_detector_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848132
# 2025-03-13T06:42:12,859 [INFO ] W-9029-drawn_humanoid_detector_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:0.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848132
# 2025-03-13T06:42:12,873 [INFO ] W-9026-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 9431
# 2025-03-13T06:42:12,874 [DEBUG] W-9026-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9026-drawn_humanoid_detector_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:12,874 [INFO ] W-9026-drawn_humanoid_detector_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:14671.0|#WorkerName:W-9026-drawn_humanoid_detector_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848132
# 2025-03-13T06:42:12,874 [INFO ] W-9026-drawn_humanoid_detector_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:1.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848132
# 2025-03-13T06:42:12,888 [INFO ] W-9021-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 9714
# 2025-03-13T06:42:12,888 [DEBUG] W-9021-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9021-drawn_humanoid_detector_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:12,888 [INFO ] W-9021-drawn_humanoid_detector_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:14694.0|#WorkerName:W-9021-drawn_humanoid_detector_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848132
# 2025-03-13T06:42:12,888 [INFO ] W-9021-drawn_humanoid_detector_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:8.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848132
# 2025-03-13T06:42:12,889 [INFO ] W-9024-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - Backend response time: 9059
# 2025-03-13T06:42:12,889 [DEBUG] W-9024-drawn_humanoid_detector_1.0 org.pytorch.serve.wlm.WorkerThread - W-9024-drawn_humanoid_detector_1.0 State change WORKER_STARTED -> WORKER_MODEL_LOADED
# 2025-03-13T06:42:12,889 [INFO ] W-9024-drawn_humanoid_detector_1.0 TS_METRICS - WorkerLoadTime.Milliseconds:14695.0|#WorkerName:W-9024-drawn_humanoid_detector_1.0,Level:Host|#hostname:a4b121b5827f,timestamp:1741848132
# 2025-03-13T06:42:12,890 [INFO ] W-9024-drawn_humanoid_detector_1.0 TS_METRICS - WorkerThreadTime.Milliseconds:1.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848132
# 2025-03-13T06:42:59,317 [INFO ] pool-3-thread-1 TS_METRICS - CPUUtilization.Percent:0.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848179
# 2025-03-13T06:42:59,318 [INFO ] pool-3-thread-1 TS_METRICS - DiskAvailable.Gigabytes:278.98909759521484|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848179
# 2025-03-13T06:42:59,318 [INFO ] pool-3-thread-1 TS_METRICS - DiskUsage.Gigabytes:164.17315292358398|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848179
# 2025-03-13T06:42:59,318 [INFO ] pool-3-thread-1 TS_METRICS - DiskUtilization.Percent:37.0|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848179
# 2025-03-13T06:42:59,318 [INFO ] pool-3-thread-1 TS_METRICS - MemoryAvailable.Megabytes:39211.9296875|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848179
# 2025-03-13T06:42:59,318 [INFO ] pool-3-thread-1 TS_METRICS - MemoryUsed.Megabytes:20273.25|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848179
# 2025-03-13T06:42:59,318 [INFO ] pool-3-thread-1 TS_METRICS - MemoryUtilization.Percent:34.8|#Level:Host|#hostname:a4b121b5827f,timestamp:1741848179


# """
