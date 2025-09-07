export default {
  name: "CommonTable",
  props: {
    data: { type: Array, default: () => [] },
    columns: { type: Array, default: () => [] }, // [{prop, label, width?, align?, type?}]
    loading: { type: Boolean, default: false },
    selectable: { type: Boolean, default: false },
    height: { type: [String, Number], default: "100%" } // 默认撑满容器
  },
  data() {
    return {
      isAllSelected: false
    };
  },
  methods: {
    handleSelectAll(val) {
      this.$emit("toggle-all", val);
    }
  },
  template: `
    <div class="common-table-wrapper">
      <el-table
        :data="data"
        stripe
        highlight-current-row
        style="width:100%"
        :height="height"
        v-loading="loading"
        header-row-class-name="common-table-header"
        @selection-change="$emit('selection-change', $event)"
        @row-click="$emit('row-click', $event)"
      >
        <!-- 多选框 -->
        <el-table-column v-if="selectable" type="selection" width="55">
          <template #header>
            <el-checkbox v-model="isAllSelected" @change="handleSelectAll" />
          </template>
        </el-table-column>

        <!-- 动态列 -->
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

          <!-- 根据type渲染不同组件 -->
          <template #default="{ row }">
            <el-input
              v-if="col.type === 'input'"
              v-model="row[col.prop]"
              size="small"
              clearable
            />
            <el-switch
              v-else-if="col.type === 'switch'"
              v-model="row[col.prop]"
            />
            <el-select
              v-else-if="col.type === 'select'"
              v-model="row[col.prop]"
              placeholder="请选择"
              size="small"
              style="width: 120px"
            >
              <el-option
                v-for="opt in col.options || []"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
            <el-date-picker
              v-else-if="col.type === 'date'"
              v-model="row[col.prop]"
              type="date"
              placeholder="选择日期"
              size="small"
            />
            <span v-else>[[ row[col.prop] ]]</span>
          </template>
        </el-table-column>

        <!-- 自定义操作列 -->
        <el-table-column
          v-if="$slots.actions"
          label="操作"
          align="center"
          width="160"
          fixed="right"
        >
          <template #default="{ row }">
            <slot name="actions" :row="row"></slot>
          </template>
        </el-table-column>
      </el-table>
    </div>
  `
};
