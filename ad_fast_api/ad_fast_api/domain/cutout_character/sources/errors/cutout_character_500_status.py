NOT_FOUND_CROPPED_IMAGE = "Failed to read cropped image from {cropped_image_path}"
NOT_FOUND_CUTOUT_CHARACTER_IMAGE = (
    "Failed to read cutout character image from {cutout_character_image_path}"
)
FAILED_TO_WRITE_CUTOUT_IMAGE = "Failed to write cutout image to {cutout_image_path}"
FAILED_TO_WRITE_MASK_IMAGE = "Failed to write mask image to {mask_image_path}"
CUTOUT_CHARACTER_IMAGE_DOES_NOT_HAVE_ALPHA_CHANNEL = (
    "Cutout character image does not have an alpha channel"
)
GET_SKELETON_TORCHSERVE_ERROR = "Failed to get skeletons, please check if the 'docker_torchserve' is running and healthy, resp: {resp}"
POSE_ESTIMATION_ERROR = "Error performing pose estimation. Check that drawn_humanoid_pose_estimator.mar was properly downloaded. Response: {pose_results}"
NO_SKELETON_DETECTED = "Could not detect any skeletons within the character bounding box. Expected exactly 1. Aborting."
MORE_THAN_ONE_SKELETON_DETECTED = "Detected {len(pose_results)} skeletons with the character bounding box. Expected exactly 1. Aborting."
