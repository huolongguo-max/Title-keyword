<template>
  <div class="mac-table-wrapper">
    <table class="mac-table">
      <thead v-if="columns.length">
        <tr>
          <th
            v-for="col in columns"
            :key="col.key"
            :style="{ width: col.width, textAlign: col.align || 'left' }"
          >
            {{ col.title }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="data.length === 0">
          <td :colspan="columns.length || 1" class="mac-table__empty">
            <slot name="empty">
              <div class="mac-table__empty-content">
                <span class="mac-table__empty-icon">📋</span>
                <span>暂无数据</span>
              </div>
            </slot>
          </td>
        </tr>
        <tr
          v-for="(row, rowIndex) in data"
          :key="rowKey ? row[rowKey] : rowIndex"
          :class="{ 'mac-table__row--clickable': clickable }"
          @click="clickable && $emit('rowClick', row, rowIndex)"
        >
          <td
            v-for="col in columns"
            :key="col.key"
            :style="{ textAlign: col.align || 'left' }"
          >
            <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]" :index="rowIndex">
              {{ row[col.key] }}
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts" generic="T extends Record<string, any>">
/**
 * MacTable - 极简风格数据表格
 * @columns 列定义 [{ key, title, width?, align? }]
 * @data 行数据
 * @rowKey 行唯一标识字段名
 * @clickable 行是否可点击
 */
export interface TableColumn {
  key: string
  title: string
  width?: string
  align?: 'left' | 'center' | 'right'
}

withDefaults(
  defineProps<{
    columns: TableColumn[]
    data: T[]
    rowKey?: string
    clickable?: boolean
  }>(),
  {
    columns: () => [],
    data: () => [],
    rowKey: '',
    clickable: false,
  }
)

defineEmits<{
  rowClick: [row: T, index: number]
}>()
</script>

<style scoped>
.mac-table-wrapper {
  overflow-x: auto;
  border-radius: var(--radius-md);
}

.mac-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

.mac-table thead th {
  padding: 10px 16px;
  text-align: left;
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid var(--color-border);
  background: transparent;
  white-space: nowrap;
}

.mac-table tbody td {
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-primary);
  transition: background var(--transition-fast);
}

.mac-table tbody tr:last-child td {
  border-bottom: none;
}

.mac-table tbody tr:hover td {
  background: rgba(0, 0, 0, 0.02);
}

.mac-table__row--clickable {
  cursor: pointer;
}

.mac-table__empty {
  text-align: center;
  padding: var(--space-xl) var(--space-md) !important;
}

.mac-table__empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
  color: var(--color-text-tertiary);
}

.mac-table__empty-icon {
  font-size: 24px;
  opacity: 0.5;
}
</style>
