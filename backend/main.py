from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# CORS 허용 (프론트를 file://이나 다른 포트에서 열어도 되게)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용이니까 일단 다 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlanRequest(BaseModel):
    days_left: int
    subjects: List[str]
    weak_subject: Optional[str] = None
    minutes_per_day: int

class SubjectPlan(BaseModel):
    subject: str
    minutes_per_day: int
    tip: str

class PlanResponse(BaseModel):
    days_left: int
    minutes_per_day: int
    plan: List[SubjectPlan]


def make_tip(subject: str, is_weak: bool) -> str:
    if subject == "math":
        base = "개념 정리 + 문제 풀이 위주로 공부해요."
    elif subject == "korean":
        base = "지문 읽기와 기출문제를 번갈아 풀어요."
    elif subject == "english":
        base = "단어 암기와 독해를 섞어서 공부해요."
    elif subject == "science":
        base = "개념을 정리한 뒤 기출 문제를 풀어요."
    elif subject == "social":
        base = "핵심 개념 암기와 기출 OX 문제를 풀어요."
    else:
        base = "핵심 개념과 기출 문제 위주로 공부해요."

    if is_weak:
        return "약한 과목이므로 매일 조금씩이라도 꼭 공부해요. " + base
    return base


@app.post("/plan", response_model=PlanResponse)
def create_plan(req: PlanRequest):
    if not req.subjects:
        # 과목이 하나도 선택되지 않았을 때
        return PlanResponse(days_left=req.days_left,
                            minutes_per_day=req.minutes_per_day,
                            plan=[])

    # 과목별 가중치: 기본 1, 약한 과목은 1.5배
    weights = []
    for s in req.subjects:
        if req.weak_subject and s == req.weak_subject:
            weights.append(1.5)
        else:
            weights.append(1.0)

    total_weight = sum(weights)

    subject_plans: List[SubjectPlan] = []
    for s, w in zip(req.subjects, weights):
        minutes = int(req.minutes_per_day * (w / total_weight))
        tip = make_tip(s, req.weak_subject == s)
        subject_plans.append(
            SubjectPlan(
                subject=s,
                minutes_per_day=minutes,
                tip=tip,
            )
        )

    return PlanResponse(
        days_left=req.days_left,
        minutes_per_day=req.minutes_per_day,
        plan=subject_plans,
    )
