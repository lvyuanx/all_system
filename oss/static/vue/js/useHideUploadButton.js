// static/vue/js/hooks/useHideUploadButton.js
const { watch, nextTick } = Vue;

/**
 * 自动隐藏 Element Plus 上传组件的上传按钮
 * @param {Ref} imageRef - common-image-upload 的 ref
 * @param {Ref<Array>} image - v-model 的图片数组
 * @param {number} limit - 上传数量上限
 */
export function useHideUploadButton(imageRef, image, limit = 1) {
  const updateUploadButton = () => {
    if (!imageRef.value || !imageRef.value.$el) return;
    const uploadDiv = imageRef.value.$el.querySelector('.el-upload.el-upload--picture-card');
    if (!uploadDiv) return;

    if (image.value.length >= limit) {
      uploadDiv.style.display = 'none';
    } else {
      uploadDiv.style.display = '';
    }
  }

  // 监听 image 数组变化
  watch(image, () => {
    nextTick(() => updateUploadButton());
  });

  // 页面初始化时也执行一次
  nextTick(() => updateUploadButton());
}

export default useHideUploadButton;