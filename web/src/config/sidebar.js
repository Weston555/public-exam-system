// 侧边栏菜单配置（学员端与管理员端）——统一管理以便固化与复用
export const studentMenu = [
  { index: '/home', icon: 'HomeFilled', label: '首页概览' },
  { index: '/goal', icon: 'Aim', label: '学习目标' },
  { index: '/plan', icon: 'Guide', label: '学习路径推荐' },
  { index: '/practice', icon: 'EditPen', label: '针对性练习' },
  { index: '/diagnostic', icon: 'DataAnalysis', label: '基线诊断' },
  { index: '/wrong', icon: 'DocumentDelete', label: '错题本' },
  { index: '/mock', icon: 'Trophy', label: '模拟考试' }
]

export const adminMenu = [
  { index: '/admin', icon: 'DataBoard', label: '数据总览' },
  { index: '/admin/syllabus', icon: 'Collection', label: '考试大纲管理' },
  { index: '/admin/knowledge', icon: 'List', label: '知识点树管理' },
  { index: '/admin/questions', icon: 'Edit', label: '题库与资源' },
  { index: '/admin/strategy', icon: 'Setting', label: '推荐策略配置' },
  { index: '/admin/users', icon: 'User', label: '用户与权限' },
  { index: '/admin/exams', icon: 'Calendar', label: '考试管理' }
]


