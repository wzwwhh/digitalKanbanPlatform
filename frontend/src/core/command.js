/**
 * Command 系统 - 统一 AI 和手动操作的执行/撤销/重做
 *
 * 设计原则：
 * - AI 操作和手动操作都输出 Command 对象
 * - 所有 Command 都可撤销/重做
 * - 用户感知不到 Command 的存在
 */
import { useHistoryStore } from '../stores/history'
import { useDashboardStore } from '../stores/dashboard'

/**
 * Command 类型常量
 */
export const CommandType = {
  ADD_WIDGET: 'ADD_WIDGET',
  UPDATE_WIDGET: 'UPDATE_WIDGET',
  DELETE_WIDGET: 'DELETE_WIDGET',
  MOVE_WIDGET: 'MOVE_WIDGET',
  RESIZE_WIDGET: 'RESIZE_WIDGET',
  BATCH: 'BATCH', // 批量操作（场景 Agent 生成多个组件）
}

/**
 * 创建 Command 对象
 * @param {string} type - CommandType 之一
 * @param {object} payload - 操作数据
 * @param {string} source - 'ai' | 'manual'
 * @returns {object} Command 对象
 */
export function createCommand(type, payload, source = 'manual') {
  return {
    type,
    payload,
    undo: null, // 执行时自动填充
    source,
    timestamp: Date.now(),
  }
}

/**
 * 执行 Command
 * @param {object} cmd - Command 对象
 */
export function executeCommand(cmd) {
  const dashboard = useDashboardStore()
  const history = useHistoryStore()

  switch (cmd.type) {
    case CommandType.ADD_WIDGET: {
      const widget = cmd.payload
      dashboard.addWidget(widget)
      cmd.undo = { type: CommandType.DELETE_WIDGET, payload: { id: widget.id } }
      break
    }
    case CommandType.UPDATE_WIDGET: {
      const { id, ...updates } = cmd.payload
      const widget = dashboard.getWidgetById(id)
      if (widget) {
        // 保存旧值用于撤销
        const oldValues = {}
        if (updates.props) {
          oldValues.props = { ...widget.props }
        }
        if (updates.position) {
          oldValues.position = { ...widget.position }
        }
        if (updates.size) {
          oldValues.size = { ...widget.size }
        }
        if (updates.dataSource !== undefined) {
          oldValues.dataSource = widget.dataSource ? { ...widget.dataSource } : null
        }
        cmd.undo = { type: CommandType.UPDATE_WIDGET, payload: { id, ...oldValues } }
        dashboard.updateWidget(id, updates)
      }
      break
    }
    case CommandType.DELETE_WIDGET: {
      const { id } = cmd.payload
      const widget = dashboard.getWidgetById(id)
      if (widget) {
        cmd.undo = { type: CommandType.ADD_WIDGET, payload: { ...widget } }
        dashboard.removeWidget(id)
      }
      break
    }
    case CommandType.MOVE_WIDGET: {
      const { id, position } = cmd.payload
      const widget = dashboard.getWidgetById(id)
      if (widget) {
        cmd.undo = {
          type: CommandType.MOVE_WIDGET,
          payload: { id, position: { ...widget.position } }
        }
        dashboard.updateWidget(id, { position })
      }
      break
    }
    case CommandType.RESIZE_WIDGET: {
      const { id, size } = cmd.payload
      const widget = dashboard.getWidgetById(id)
      if (widget) {
        cmd.undo = {
          type: CommandType.RESIZE_WIDGET,
          payload: { id, size: { ...widget.size } }
        }
        dashboard.updateWidget(id, { size })
      }
      break
    }
    case CommandType.BATCH: {
      const results = cmd.payload.commands.map(subCmd => {
        executeCommand(subCmd)
        return subCmd
      })
      cmd.undo = {
        type: CommandType.BATCH,
        payload: {
          commands: results.map(c => c.undo).filter(Boolean).reverse()
        }
      }
      break
    }
  }

  history.push(cmd)
}

/**
 * 撤销
 */
export function undo() {
  const history = useHistoryStore()
  const cmd = history.popUndo()
  if (cmd && cmd.undo) {
    // 执行撤销但不入栈
    executeUndoRedo(cmd.undo)
    history.pushRedo(cmd)
  }
}

/**
 * 重做
 */
export function redo() {
  const history = useHistoryStore()
  const cmd = history.popRedo()
  if (cmd) {
    executeCommand(cmd)
  }
}

/**
 * 内部方法：执行撤销/重做操作（不入 history 栈）
 */
function executeUndoRedo(undoCmd) {
  const dashboard = useDashboardStore()

  switch (undoCmd.type) {
    case CommandType.ADD_WIDGET:
      dashboard.addWidget(undoCmd.payload)
      break
    case CommandType.DELETE_WIDGET:
      dashboard.removeWidget(undoCmd.payload.id)
      break
    case CommandType.UPDATE_WIDGET: {
      const { id, ...updates } = undoCmd.payload
      dashboard.updateWidget(id, updates)
      break
    }
    case CommandType.MOVE_WIDGET: {
      const { id, position } = undoCmd.payload
      dashboard.updateWidget(id, { position })
      break
    }
    case CommandType.RESIZE_WIDGET: {
      const { id, size } = undoCmd.payload
      dashboard.updateWidget(id, { size })
      break
    }
    case CommandType.BATCH: {
      undoCmd.payload.commands.forEach(c => executeUndoRedo(c))
      break
    }
  }
}
