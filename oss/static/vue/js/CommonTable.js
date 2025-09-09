export default {
  name: "CommonTable",
  props: {
    data: { type: Array, default: () => [] },
    columns: { type: Array, default: () => [] },
    loading: { type: Boolean, default: false },
    selectable: { type: Boolean, default: false },
    height: { type: [String, Number], default: "100%" },
    isPaginated: { type: Boolean, default: false },
    currentPage: { type: Number, default: 1 },
    pageSize: { type: Number, default: 10 },
    totalCount: { type: Number, default: 0 }
  },
  data() {
    return {
      isAllSelected: false,
      localCurrentPage: this.currentPage,
      localPageSize: this.pageSize,
      localTotalCount: this.totalCount
    };
  },
  computed: {
    paginatedData() {
        
      return this.data;
    }
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
      this.localCurrentPage = 1; // pageSize改变重置第一页
      this.emitPageChange();
    },
    emitPageChange() {
      this.$emit("update:currentPage", this.localCurrentPage);
      this.$emit("update:pageSize", this.localPageSize);
      this.$emit("update:totalCount", this.localTotalCount);
      this.$emit("page-change");
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
      <el-table
        :data="paginatedData"
        stripe
        highlight-current-row
        style="width:100%"
        :height="height"
        v-loading="loading"
        header-row-class-name="common-table-header"
        @selection-change="$emit('selection-change', $event)"
        @row-click="$emit('row-click', $event)"
      >
        <el-table-column v-if="selectable" type="selection" width="55">
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
