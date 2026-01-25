// Mock 数据统一管理（用于演示模式）
export const sampleQuestions = [
  {
    id: 1,
    type: "SINGLE",
    stem: "下列哪个选项是正确的？",
    options_json: ["A. 选项一", "B. 选项二", "C. 选项三", "D. 选项四"],
    answer_json: ["A"],
    analysis: "因为 A 是正确的。",
    difficulty: 2,
    knowledge_points: [{ id: 101, name: "常识判断" }]
  },
  {
    id: 2,
    type: "MULTI",
    stem: "请选择所有正确项。",
    options_json: ["A. 甲", "B. 乙", "C. 丙", "D. 丁"],
    answer_json: ["A", "C"],
    analysis: "A 和 C 都是正确的。",
    difficulty: 3,
    knowledge_points: [{ id: 102, name: "言语理解" }]
  },
  {
    id: 3,
    type: "JUDGE",
    stem: "下列说法正确？（正确/错误）",
    options_json: [],
    answer_json: ["T"],
    analysis: "该说法为真。",
    difficulty: 1,
    knowledge_points: [{ id: 103, name: "判断推理" }]
  },
  {
    id: 4,
    type: "FILL",
    stem: "填空：首都为____。",
    options_json: [],
    answer_json: ["北京"],
    analysis: "首都是北京。",
    difficulty: 2,
    knowledge_points: [{ id: 104, name: "资料分析" }]
  },
  {
    id: 5,
    type: "SHORT",
    stem: "请简述公考备考的核心要点。",
    options_json: [],
    answer_json: [],
    analysis: "核心要点为稳扎稳打、精练真题、查漏补缺。",
    difficulty: 4,
    knowledge_points: [{ id: 105, name: "申论写作" }]
  }
]

export const sampleExam = {
  id: 1001,
  title: "演示诊断卷",
  category: "DIAGNOSTIC",
  duration_minutes: 30,
  paper_id: 2001
}

export const sampleAttempt = (examId = 1001) => {
  return {
    attempt_id: 5000 + examId,
    status: "DOING",
    started_at: new Date().toISOString(),
    exam: { id: examId, title: sampleExam.title, duration_minutes: sampleExam.duration_minutes },
    questions: sampleQuestions.map((q, idx) => ({
      id: q.id,
      order_no: idx + 1,
      question: {
        id: q.id,
        type: q.type,
        stem: q.stem,
        options_json: q.options_json
      },
      saved_answer: null
    }))
  }
}

export const sampleOverview = {
  plan_completion_rate: 0,
  avg_mastery: 0,
  wrong_due_count: 0,
  last_score: null
}

export const sampleModuleMastery = {
  subject: "XINGCE",
  items: [
    { module: "常识判断", code: "CS", mastery: 0.0 },
    { module: "言语理解与表达", code: "YY", mastery: 0.0 },
    { module: "数量关系", code: "SL", mastery: 0.0 },
    { module: "判断推理", code: "PD", mastery: 0.0 },
    { module: "资料分析", code: "ZL", mastery: 0.0 }
  ]
}

export const sampleScoreTrend = {
  items: [
    { submitted_at: new Date().toISOString(), total_score: 80 }
  ]
}

export const sampleGoals = {
  id: 1,
  exam_date: "2026-12-01",
  target_score: 120,
  daily_minutes: 120
}

export const samplePlans = {
  plan_id: 1,
  start_date: new Date().toISOString(),
  end_date: new Date(Date.now() + 7 * 24 * 3600 * 1000).toISOString(),
  items_by_date: {
    [new Date().toISOString().slice(0, 10)]: [
      { id: 1, date: new Date().toISOString().slice(0, 10), type: "LEARN", knowledge_id: 101, expected_minutes: 60, status: "TODO" }
    ]
  }
}

export const sampleWrongQuestions = [
  { id: 901, question_id: 1, last_wrong_at: new Date().toISOString(), next_review_at: new Date().toISOString() }
]


