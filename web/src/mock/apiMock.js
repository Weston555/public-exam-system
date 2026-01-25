import {
  sampleQuestions,
  sampleExam,
  sampleAttempt,
  sampleOverview,
  sampleModuleMastery,
  sampleScoreTrend,
  sampleGoals,
  samplePlans,
  sampleWrongQuestions
} from './mockData'

// 简单的 path 匹配助手
const urlPath = (url = '') => {
  try {
    const u = new URL(url, window.location.origin)
    return u.pathname + u.search
  } catch (e) {
    return url
  }
}

export function handleMock(config) {
  const path = urlPath(config.url)
  const method = (config.method || 'get').toLowerCase()

  // auth 登录
  if (path.includes('/api/v1/auth/login') && method === 'post') {
    return {
      access_token: 'demo-token-' + Date.now(),
      token_type: 'bearer',
      role: (config.data && JSON.parse(config.data).role || 'STUDENT').toLowerCase(),
      expires_in: 1800
    }
  }

  // 首页相关
  if (path.includes('/api/v1/analytics/student/overview') && method === 'get') {
    return sampleOverview
  }

  if (path.includes('/api/v1/analytics/student/score-trend') && method === 'get') {
    return sampleScoreTrend
  }

  if (path.includes('/api/v1/analytics/student/mastery-top') && method === 'get') {
    return { items: sampleQuestions.slice(0, 3).map(q => ({ knowledge_id: q.knowledge_points[0].id, name: q.knowledge_points[0].name, mastery: Math.round(Math.random() * 100) })) }
  }

  if (path.includes('/api/v1/analytics/student/module-mastery') && method === 'get') {
    return sampleModuleMastery
  }

  // goals
  if (path.includes('/api/v1/goals/me') && method === 'get') {
    return sampleGoals
  }
  if (path.includes('/api/v1/goals') && (method === 'post' || method === 'put')) {
    return { message: 'ok', goal: sampleGoals }
  }

  // plans
  if (path.includes('/api/v1/plans/active') && method === 'get') {
    return samplePlans
  }
  if (path.includes('/api/v1/plans/generate') && method === 'post') {
    return { plan_id: samplePlans.plan_id, ...samplePlans }
  }
  if (path.match(/\/api\/v1\/plans\/items\/\d+\/start/) && method === 'post') {
    return { message: 'started' }
  }
  if (path.match(/\/api\/v1\/plans\/items\/\d+/) && method === 'patch') {
    return { message: 'updated' }
  }

  // knowledge / practice
  if (path.includes('/api/v1/knowledge/tree') && method === 'get') {
    return [{ id: 100, name: '公务员考试', children: [{ id: 101, name: '行测' }] }]
  }
  if (path.includes('/api/v1/practice/generate') && method === 'post') {
    return { exam_id: sampleExam.id }
  }

  // exams / diagnostic / mock
  if (path.includes('/api/v1/exams') && method === 'get') {
    // support ?category=DIAGNOSTIC or MOCK
    if (path.includes('category=DIAGNOSTIC')) return { items: [sampleExam] }
    if (path.includes('category=MOCK')) return { items: [sampleExam] }
    return { items: [sampleExam] }
  }

  if (path.match(/\/api\/v1\/exams\/\d+\/start/) && method === 'post') {
    const examIdMatch = path.match(/\/exams\/(\d+)\/start/)
    const examId = examIdMatch ? Number(examIdMatch[1]) : sampleExam.id
    return sampleAttempt(examId)
  }

  // wrong questions
  if (path.includes('/api/v1/wrong-questions') && method === 'get') {
    return { items: sampleWrongQuestions }
  }
  if (path.includes('/api/v1/wrong-questions/review/generate') && method === 'post') {
    return { exam_id: sampleExam.id }
  }

  // attempts/history
  if (path.includes('/api/v1/attempts/history') && method === 'get') {
    return { items: [{ attempt_id: sampleAttempt().attempt_id, total_score: 80, exam_id: sampleExam.id }] }
  }

  // attempts detail / answer / submit / result
  if (path.match(/\/api\/v1\/attempts\/\d+$/) && method === 'get') {
    const match = path.match(/\/api\/v1\/attempts\/(\d+)$/)
    const attemptId = match ? Number(match[1]) : sampleAttempt().attempt_id
    return sampleAttempt(sampleExam.id)
  }
  if (path.match(/\/api\/v1\/attempts\/\d+\/answer/) && (method === 'post' || method === 'patch')) {
    return { message: 'saved' }
  }
  if (path.match(/\/api\/v1\/attempts\/\d+\/submit/) && method === 'post') {
    return { attempt_id: sampleAttempt().attempt_id, total_score: 85.5, correct_count: 3, total_questions: sampleQuestions.length, submitted_at: new Date().toISOString(), results: sampleQuestions.map(q => ({ question_id: q.id, is_correct: Math.random() > 0.5, score_awarded: 2.0, correct_answer: q.answer_json, user_answer: [] })) }
  }
  if (path.match(/\/api\/v1\/attempts\/\d+\/result/) && method === 'get') {
    return { attempt_id: sampleAttempt().attempt_id, results: sampleQuestions.map(q => ({ question_id: q.id, is_correct: Math.random() > 0.5, score_awarded: 2.0, correct_answer: q.answer_json, user_answer: [] })) }
  }

  // fallback: return empty success
  return {}
}


