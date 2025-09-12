export default {
  name: "CommonTable",
  props: {
    data: { type: Array, default: () => [] },
    columns: { type: Array, default: () => [] },
    loading: { type: Boolean, default: false },
    selectableIsShow: { type: Boolean, default: false },  // 是否显示多选按框
    selectable : { type: Function, default: (row, rowIdx) => true },
    height: { type: [String, Number], default: "100%" },
    isPaginated: { type: Boolean, default: false },
    currentPage: { type: Number, default: 1 },
    pageSize: { type: Number, default: 10 },
    totalCount: { type: Number, default: 0 },
    filterForm: { type: Object, default: () => ({}) }, // 父组件传入
    rowClassName: { type: [String, Function], default: "" },
  },
  data() {
    return {
      isAllSelected: false,
      localCurrentPage: this.currentPage,
      localPageSize: this.pageSize,
      localTotalCount: this.totalCount,
      localFilterForm: { ...this.filterForm } // 内部可修改
    };
  },
  watch: {
    currentPage(val) {
      this.localCurrentPage = val;
    },
    pageSize(val) {
      this.localPageSize = val;
    },
    totalCount(val) {
      this.localTotalCount = val;
    },
    filterForm: {
      handler(val) {
        this.localFilterForm = { ...val };
      },
      deep: true
    }
  },
  computed: {
    paginatedData() {
      return this.data;
    }
  },
  methods: {
    handleSelectAll(val) {
      this.$emit("toggle-all", val);
    },
    handleCurrentPageChange(page) {
      this.localCurrentPage = page;
      this.emitPageChange();
    },
    handlePageSizeChange(size) {
      this.localPageSize = size;
      this.localCurrentPage = 1;
      this.emitPageChange();
    },
    emitPageChange() {
      this.$emit("update:currentPage", this.localCurrentPage);
      this.$emit("update:pageSize", this.localPageSize);
      this.$emit("update:totalCount", this.localTotalCount);
      this.$emit("update:filterForm", this.localFilterForm); // 双向绑定过滤条件
      this.$emit("page-change", { 
        page: this.localCurrentPage, 
        size: this.localPageSize, 
        filters: this.localFilterForm 
      });
    },
    handleFilterSubmit() {
      this.localCurrentPage = 1;
      this.emitPageChange();
    },
    handleFilterReset() {
      this.localFilterForm = {};
      this.localCurrentPage = 1;
      this.emitPageChange();
    },
    // 外部调用重置方法
    resetFilters() {
        this.handleFilterReset();
        this.$emit("page-change")
    },
    // 获取表格实例
    getTableRef() {
      return this.$refs.innerTable;
    }
  },
  mounted() {
    if (this.isPaginated) {
      this.localCurrentPage = this.currentPage || 1;
      this.localPageSize = this.pageSize || 15;
      this.localTotalCount = this.totalCount || 0;
    }
  },
  template: `
    <div class="common-table-wrapper">

      <!-- 过滤表单区域 -->
      <div v-if="$slots.filter" class="common-table-filter">
        <el-form :model="localFilterForm" size="small" inline>
          <slot name="filter" :model="localFilterForm"></slot>
          <el-form-item>
            <el-button type="primary" @click="handleFilterSubmit" :disabled="loading"><el-icon><Search /></el-icon>搜索</el-button>
            <el-button @click="handleFilterReset" :disabled="loading"><el-icon><Refresh /></el-icon>重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 表格 -->
      <el-table
        ref="innerTable"
        :data="paginatedData"
        stripe
        highlight-current-row
        style="width:100%"
        :height="height"
        v-loading="loading"
        header-row-class-name="common-table-header"
        :row-class-name="rowClassName"
        @selection-change="$emit('selection-change', $event)"
        @row-click="$emit('row-click', $event)"
      >
        <el-table-column v-if="selectableIsShow" :selectable="selectable" type="selection" fixed="left" width="55">
          <template #header>
            <el-checkbox v-model="isAllSelected" @change="handleSelectAll" />
          </template>
        </el-table-column>

        <el-table-column
          v-for="col in columns"
          :key="col.prop"
          :prop="col.prop"
          :label="col.label"
          :width="col.width"
          :align="col.align || 'left'"
          :fixed="col.fixed ? col.fixed : false"
          show-overflow-tooltip
        >
          <template #header>
            <span class="common-table-header-label">[[ col.label ]]</span>
          </template>
          <template #default="{ row }">
            <el-input v-if="col.type === 'input'" v-model="row[col.prop]" size="small" clearable />
            <el-switch v-else-if="col.type === 'switch'" v-model="row[col.prop]" />
            <el-select v-else-if="col.type === 'select'" v-model="row[col.prop]" placeholder="请选择" size="small" style="width:120px">
              <el-option v-for="opt in col.options || []" :key="opt.value" :label="opt.label" :value="opt.value" />
            </el-select>
            <el-date-picker v-else-if="col.type === 'date'" v-model="row[col.prop]" type="date" placeholder="选择日期" size="small" />
            <span v-else>[[ row[col.prop] ]]</span>
          </template>
        </el-table-column>

        <el-table-column v-if="$slots.actions" label="操作" align="center" width="160" fixed="right">
          <template #default="{ row }">
            <slot name="actions" :row="row"></slot>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="common-table-pagination">
        <el-pagination
          v-if="isPaginated"
          background
          :current-page="localCurrentPage"
          :page-size="localPageSize"
          :page-sizes="[15,30,50,100]"
          :total="localTotalCount"
          layout="total, sizes, prev, pager, next"
          @current-change="handleCurrentPageChange"
          @size-change="handlePageSizeChange"
        />
      </div>
    </div>
  `
};
