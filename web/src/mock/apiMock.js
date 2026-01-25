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

// in-memory storage for attempts and answers (persisted to localStorage for demo stability)
const ATTEMPTS_KEY = 'demo_attempts_v1'
let attemptsStore = {}

// load persisted attempts from localStorage
try {
  const raw = localStorage.getItem(ATTEMPTS_KEY)
  if (raw) {
    attemptsStore = JSON.parse(raw) || {}
  }
} catch (e) {
  attemptsStore = {}
}

function persistAttempts() {
  try {
    localStorage.setItem(ATTEMPTS_KEY, JSON.stringify(attemptsStore))
  } catch (e) {
    // ignore
  }
}

export function handleMock(config) {
  // support axios config.params by appending to url for parsing
  let fullUrl = config.url
  if (config.params) {
    const usp = new URLSearchParams(config.params).toString()
    if (usp) {
      fullUrl = fullUrl + (fullUrl.includes('?') ? '&' : '?') + usp
    }
  }
  const path = urlPath(fullUrl)
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
    // create and persist attempt
    const att = sampleAttempt(examId)
    attemptsStore[att.attempt_id] = att
    persistAttempts()
    return att
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
    // return persisted attempt if exists, else create one for sampleExam
    if (attemptsStore[attemptId]) return attemptsStore[attemptId]
    const att = sampleAttempt(sampleExam.id)
    attemptsStore[att.attempt_id] = att
    persistAttempts()
    return att
  }
  if (path.match(/\/api\/v1\/attempts\/\d+\/answer/) && (method === 'post' || method === 'patch')) {
    const match = path.match(/\/api\/v1\/attempts\/(\d+)\/answer/)
    const attemptId = match ? Number(match[1]) : null
    const body = config.data ? (typeof config.data === 'string' ? JSON.parse(config.data) : config.data) : {}
    // support saving by question_id
    if (attemptId && attemptsStore[attemptId]) {
      attemptsStore[attemptId].questions = attemptsStore[attemptId].questions.map(q => {
        if (q.question.id === body.question_id || q.question.id === body.questionId) {
          q.saved_answer = body.answer_json || body.answer || body.user_answer || null
        }
        return q
      })
      persistAttempts()
    }
    return { message: 'saved' }
  }
  if (path.match(/\/api\/v1\/attempts\/\d+\/submit/) && method === 'post') {
    const match = path.match(/\/api\/v1\/attempts\/(\d+)\/submit/)
    const attemptId = match ? Number(match[1]) : null
    const att = attemptId ? attemptsStore[attemptId] : null
    const results = []
    let total_score = 0
    if (att) {
      for (const q of att.questions) {
        const correct = sampleQuestions.find(s => s.id === q.question.id)
        let is_correct = false
        const user_answer = q.saved_answer || []
        const correct_ans = correct ? correct.answer_json || [] : []
        if (correct && correct.type === 'SINGLE') {
          is_correct = (user_answer && user_answer[0] && String(user_answer[0]).toUpperCase() === String(correct_ans[0]).toUpperCase())
        } else if (correct && correct.type === 'MULTI') {
          const ua = new Set((user_answer || []).map(x => String(x).toUpperCase()))
          const ca = new Set((correct_ans || []).map(x => String(x).toUpperCase()))
          is_correct = ua.size === ca.size && [...ua].every(x => ca.has(x))
        } else if (correct && correct.type === 'JUDGE') {
          is_correct = (user_answer && String(user_answer[0]).toUpperCase() === String(correct_ans[0]).toUpperCase())
        } else {
          // fallback: false
          is_correct = false
        }
        const score_awarded = is_correct ? 2.0 : 0.0
        total_score += score_awarded
        results.push({ question_id: q.question.id, is_correct, score_awarded, correct_answer: correct_ans, user_answer: user_answer })
      }
      att.status = 'SUBMITTED'
      att.submitted_at = new Date().toISOString()
      att.total_score = total_score
      attemptsStore[attemptId] = att
      persistAttempts()
    }
    return { attempt_id: att ? att.attempt_id : sampleAttempt().attempt_id, total_score: total_score, correct_count: results.filter(r => r.is_correct).length, total_questions: results.length, submitted_at: new Date().toISOString(), results }
  }
  if (path.match(/\/api\/v1\/attempts\/\d+\/result/) && method === 'get') {
    const match = path.match(/\/api\/v1\/attempts\/(\d+)\/result/)
    const attemptId = match ? Number(match[1]) : null
    const att = attemptId ? attemptsStore[attemptId] : null
    if (att && att.status === 'SUBMITTED') {
      return { attempt_id: att.attempt_id, results: att.questions.map(q => ({ question_id: q.question.id, is_correct: Math.random() > 0.5, score_awarded: 2.0, correct_answer: (sampleQuestions.find(s=>s.id===q.question.id)||{}).answer_json || [], user_answer: q.saved_answer })) }
    }
    // fallback
    return { attempt_id: sampleAttempt().attempt_id, results: sampleQuestions.map(q => ({ question_id: q.id, is_correct: Math.random() > 0.5, score_awarded: 2.0, correct_answer: q.answer_json, user_answer: [] })) }
  }

  // fallback: return empty success
  return {}
}


