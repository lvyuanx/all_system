export function createDesignerNodeItem(ComponentPreview) {
    return {
        name: "DesignerNodeItem",
        components: {
            ComponentPreview,
        },
        props: {
            node: { type: Object, required: true },
            selectedNodeId: { type: String, default: "" },
            componentLabel: { type: Function, required: true },
            selectNode: { type: Function, required: true },
            moveNode: { type: Function, required: true },
            copyNode: { type: Function, required: true },
            removeNode: { type: Function, required: true },
            onNodeDragStart: { type: Function, required: true },
            onNodeDrop: { type: Function, required: true },
            onContainerDrop: { type: Function, required: true },
            onContainerDragOver: { type: Function, required: true },
            onContainerDragLeave: { type: Function, required: true },
            isContainerDropActive: { type: Function, required: true },
            onNodeDragEnter: { type: Function, required: true },
            isNodeDropTarget: { type: Function, required: true },
            containerStyle: { type: Function, required: true },
            childMode: { type: Boolean, default: false },
        },
        template: `
            <div
                :class="[childMode ? 'fd-child' : 'fd-node', { active: selectedNodeId === node.id, 'fd-drop-before': isNodeDropTarget(node.id) }]"
                draggable="true"
                @dragstart.stop="onNodeDragStart(node.id)"
                @dragenter.stop.prevent="onNodeDragEnter(node.id)"
                @dragover.prevent
                @drop.stop="onNodeDrop(node.id)">
                <div class="fd-node-head" @click.stop="selectNode(node.id)">
                    <div class="fd-node-title">
                        <el-tag size="small">[[ componentLabel(node.component) ]]</el-tag>
                        <span>[[ node.label || node.key || '未命名组件' ]]</span>
                    </div>
                    <div class="fd-node-actions">
                        <el-button link @click.stop="moveNode(node.id, -1)" title="上移"><el-icon><Top /></el-icon></el-button>
                        <el-button link @click.stop="moveNode(node.id, 1)" title="下移"><el-icon><Bottom /></el-icon></el-button>
                        <el-button link @click.stop="copyNode(node.id)" title="复制"><el-icon><CopyDocument /></el-icon></el-button>
                        <el-button link type="danger" @click.stop="removeNode(node.id)" title="删除"><el-icon><Delete /></el-icon></el-button>
                    </div>
                </div>
                <div class="fd-node-body">
                    <template v-if="node.component === 'container'">
                        <div
                            class="fd-container"
                            :class="{ 'fd-drop-active': isContainerDropActive(node.id) }"
                            :style="containerStyle(node)"
                            @dragenter.stop.prevent="onContainerDragOver(node.id)"
                            @dragover.stop.prevent="onContainerDragOver(node.id)"
                            @dragleave.stop="onContainerDragLeave($event, node.id)"
                            @drop.stop="onContainerDrop(node.id)">
                            <div v-if="!(node.children || []).length" class="fd-container-empty">拖字段到容器内</div>
                            <designer-node-item
                                v-for="child in (node.children || [])"
                                :key="child.id"
                                :node="child"
                                :selected-node-id="selectedNodeId"
                                :component-label="componentLabel"
                                :select-node="selectNode"
                                :move-node="moveNode"
                                :copy-node="copyNode"
                                :remove-node="removeNode"
                                :on-node-drag-start="onNodeDragStart"
                                :on-node-drop="onNodeDrop"
                                :on-container-drop="onContainerDrop"
                                :on-container-drag-over="onContainerDragOver"
                                :on-container-drag-leave="onContainerDragLeave"
                                :is-container-drop-active="isContainerDropActive"
                                :on-node-drag-enter="onNodeDragEnter"
                                :is-node-drop-target="isNodeDropTarget"
                                :container-style="containerStyle"
                                :child-mode="true"></designer-node-item>
                        </div>
                    </template>
                    <template v-else>
                        <component-preview :node="node" :component-label="componentLabel"></component-preview>
                    </template>
                </div>
            </div>
        `,
    };
}
