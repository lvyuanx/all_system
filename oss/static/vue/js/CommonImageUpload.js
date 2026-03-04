export default {
  name: "CommonImageUpload",

  props: {
    modelValue: { type: Array, default: () => [] }, // 多文件数组
    maxSize: { type: Number, default: 5 },          // 单张图片最大 MB
    limit: { type: Number, default: 5 },           // 最大上传数量
    disabled: { type: Boolean, default: false }
  },

  data() {
    const { ElMessage } = window.SimpleUIExtra;
    return {
      fileList: [...this.modelValue], // 上传文件列表
      previewVisible: false,
      previewUrl: "",
      $message: ElMessage
    };
  },

  watch: {
    // 外部 v-model 变化时同步更新内部 fileList
    modelValue(val) {
      this.fileList = [...val];
    }
  },

  methods: {
    handleExceed(files, fileList) {
      this.$message.error(`最多只能上传 ${this.limit} 张图片`);
    },

    handleChange(file, fileListInner) {
      const rawFile = file.raw;
      if (!rawFile) return;

      const isImage = rawFile.type.startsWith("image/");
      const isValidSize = rawFile.size / 1024 / 1024 <= this.maxSize;

      if (!isImage) {
        this.$message.error("只能上传图片文件");
        return;
      }

      if (!isValidSize) {
        this.$message.error(`图片不能超过 ${this.maxSize}MB`);
        return;
      }

      if (fileListInner.length > this.limit) {
        this.$message.error(`最多只能上传 ${this.limit} 张图片`);
        return;
      }

      this.fileList = fileListInner;
      this.$emit("update:modelValue", fileListInner);
    },

    handleRemove(file, fileListInner) {
      this.fileList = fileListInner;
      this.$emit("update:modelValue", fileListInner);
    },

    handlePreview(file) {
      this.previewUrl = file.url || URL.createObjectURL(file.raw);
      this.previewVisible = true;
    }
  },

  template: `
    <div>
      <el-upload
        list-type="picture-card"
        :auto-upload="false"
        :file-list="fileList"
        :on-exceed="handleExceed"
        :limit="limit"
        :disabled="disabled"
        :on-change="handleChange"
        :on-remove="handleRemove"
        :on-preview="handlePreview"
        class="multi-upload"
      >
          <el-icon><Plus /></el-icon>
      </el-upload>

      <el-dialog v-model="previewVisible" width="50%">
        <img :src="previewUrl" style="width: 100%" />
      </el-dialog>
    </div>
  `
};