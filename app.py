import csv, io, os, base64, html
import streamlit as st

# ----------------------------
# 배경: bg.jpg를 Base64로 CSS 주입 (경로 문제 무력화)
# ----------------------------
def inject_background(base_dir: str, filename: str = "bg.jpg"):
    """
    주어진 디렉터리에서 배경 이미지 파일을 읽어
    Base64로 인코딩한 뒤 Streamlit 앱의 배경으로 설정합니다.

    Args:
        base_dir (str): 이미지 파일이 위치한 기본 디렉터리
        filename (str): 배경 이미지 파일명 (기본값: 'bg.jpg')
    """
    path = os.path.join(base_dir, filename)
    if not os.path.exists(path):
        # 배경 이미지를 찾을 수 없으면 아무 것도 하지 않습니다.
        return
    # 이미지 파일을 읽어 Base64로 인코딩합니다.
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    # CSS를 통해 앱의 배경에 이미지를 적용합니다.
    # Streamlit 버전에 따라 내부 CSS 구조가 변할 수 있으므로, 최상위 .stApp 클래스에 배경 이미지를 지정합니다.
    # 반복 패턴이 있는 배경 이미지는 repeat 옵션을 사용하여 화면 전체에 자연스럽게 채웁니다.
    st.markdown(
        f"""
        <style>
        /* 전체 앱 배경 지정 */
        .stApp {{
            background-image: url("data:image/jpg;base64,{b64}");
            background-repeat: repeat;
            background-position: center;
            background-size: contain;
           
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# ----------------------------
# CSV 로더 (pandas 미사용, BOM/빈줄 방어)
# ----------------------------
def load_questions(csv_path: str):
    """
    CSV 파일에서 퀴즈 문항을 로드합니다. pandas를 사용하지 않고
    Python 내장 csv 모듈을 이용하여 BOM과 빈줄을 방지합니다.

    Args:
        csv_path (str): CSV 파일의 경로

    Returns:
        list[dict]: 정렬된 문항 리스트
    """
    if not os.path.exists(csv_path):
        st.error(f"CSV 파일을 찾을 수 없습니다: {csv_path}")
        st.stop()

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        raw = f.read().splitlines()
    # 빈 줄을 제거합니다.
    lines = [ln for ln in raw if ln.strip() != ""]
    if not lines:
        st.error("CSV에 데이터가 없습니다.")
        st.stop()

    buf = io.StringIO("\n".join(lines))
    dr = csv.DictReader(buf)

    # 헤더의 BOM 제거
    clean_names = [(fn or "").lstrip("\ufeff") for fn in (dr.fieldnames or [])]
    field_map = {clean: orig for clean, orig in zip(clean_names, dr.fieldnames)}

    def get(row, key, default=""):
        real = field_map.get(key, key)
        return (row.get(real, default) or "").strip()

    items = []
    for r in dr:
        items.append({
            "id": get(r, "id"),
            "question": get(r, "question"),
            "type": get(r, "type"),
            "image": get(r, "image"),
            "choices": [get(r, "choice1"), get(r, "choice2"), get(r, "choice3")],
            "answer": get(r, "answer"),
        })

    def safe_int(x):
        try:
            return int(x)
        except:
            return 10 ** 9
    # id 순으로 정렬합니다.
    items.sort(key=lambda q: safe_int(q["id"]))
    return items

# ----------------------------
# 채점
# ----------------------------
def judge(user_answer: str, correct_answer: str, qtype: str) -> bool:
    """
    사용자 답안과 정답을 비교하여 맞았는지 여부를 반환합니다.

    Args:
        user_answer (str): 사용자가 입력한 답안
        correct_answer (str): 실제 정답
        qtype (str): 문제 유형 ('주관식' 또는 '객관식')

    Returns:
        bool: 정답 여부
    """
    ua = (user_answer or "").strip()
    ca = (correct_answer or "").strip()
    if qtype == "주관식":
        # 대소문자를 구분하지 않습니다.
        return ua.lower() == ca.lower()
    return ua == ca

# ----------------------------
# 결과 티어
# ----------------------------
def result_tier(score: int):
    """
    점수에 따라 표시할 결과 이미지와 메시지를 결정합니다.

    Args:
        score (int): 맞은 문제 수

    Returns:
        tuple[str, str]: (이미지 파일명, 메시지)
    """
    if score <= 5:
        return "result1.png", "오.. 아직 MZ 감성 입문! 다음엔 더 잘하실 수 있어요 😉"
    if 6 <= score <= 10:
        return "result2.png", "좋아요! 감이 오기 시작했어요 😎"
    if 11 <= score <= 15:
        return "result3.png", "우와! 꽤나 MZ 트렌디하신데요? 🔥"
    return "result4.png", "완벽! 당신은 거의 MZ 그 자체 🙌"

# ----------------------------
# 공통 스타일
# ----------------------------
def inject_css():
    """
    앱 전반에 적용할 CSS 스타일을 주입합니다.
    """
    st.markdown(
        """
        <style>
        h1, [data-testid="stHeader"] h1, .st-emotion-cache-10trblm {
            text-align: center !important; font-weight: 800 !important;
        }
        .top-nav { display:flex; gap:8px; justify-content:center; flex-wrap:wrap; margin:8px auto 18px; }
        .top-nav .chip {
            min-width:28px; height:28px; padding:0 8px; border-radius:6px;
            border:1px solid #d8dbe4; background:#fff; color:#222;
            display:inline-flex; align-items:center; justify-content:center;
            font-weight:600; box-shadow:0 1px 1px rgba(0,0,0,.04);
        }
        .top-nav .chip.active { background:#b89cff; color:#fff; border-color:#b89cff; }
        .question-banner {
            width:650px; max-width:92vw; margin:0 auto 14px; padding:16px 18px;
            background:#ffffffee; border:1px solid #e8e9f1; border-radius:12px;
            box-shadow:0 6px 20px rgba(0,0,0,.06); text-align:center;
            font-size:18px; font-weight:700; line-height:1.4;
        }
        .stForm {
            width:650px; max-width:92vw; margin:0 auto; padding:16px !important;
            border:1px solid #e8e9f1 !important; border-radius:12px !important;
            box-shadow:0 6px 20px rgba(0,0,0,.06) !important; background:rgba(255,255,255,.98) !important;
        }
        .stImage img {
            max-width:650px !important; width:650px !important; height:auto !important;
            display:block; margin:0 auto; border-radius:10px; box-shadow:0 4px 16px rgba(0,0,0,.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# ----------------------------
# 메인
# ----------------------------
def main():
    """
    Streamlit 앱의 메인 함수. 퀴즈 시작부터 결과 표시까지의 모든 로직을 처리합니다.
    """
    st.set_page_config(page_title="MZ 테스트", page_icon="🧪", layout="centered")

    # 현재 파일의 디렉터리
    base_dir = os.path.dirname(__file__)
    # 배경 이미지 주입
    inject_background(base_dir)     # bg.jpg → Base64 주입
    # 공통 CSS 스타일 주입
    inject_css()

    # 퀴즈 문제 로드
    questions = load_questions(os.path.join(base_dir, "mz_test.csv"))
    total = len(questions)

    ss = st.session_state
    if "page" not in ss:
        ss.page = 0         # 0: 시작, 1..N: 문제, N+1: 결과
    if "answers" not in ss:
        ss.answers = {}  # {id: answer}
    if "username" not in ss:
        ss.username = ""

    # 시작 페이지
    if ss.page == 0:
        st.title("MZ 테스트")
        st.write("MZ 신조어/밈 이해도를 확인해보세요. 이름을 입력하면 결과에 표시됩니다.")
        ss.username = st.text_input("이름을 입력하세요", value=ss.username)
        if st.button("시작하기"):
            ss.page = 1
            st.rerun()
        return

    # 문제 페이지
    if 1 <= ss.page <= total:
        q = questions[ss.page - 1]
        disp_no = ss.page

        # 네비게이션
        chips = []
        for n in range(1, total + 1):
            cls = "chip active" if n == disp_no else "chip"
            chips.append(f'<span class="{cls}">{n}</span>')
        st.markdown(f'<div class="top-nav">{"".join(chips)}</div>', unsafe_allow_html=True)

        # 질문 배너
        question_text = (q.get("question") or "").strip()
        st.markdown(
            f'<div class="question-banner">{html.escape(question_text) if question_text else f"문제 {disp_no}"}</div>',
            unsafe_allow_html=True,
        )

        # 문제 이미지 (경고 없이 width만 사용)
        img_file = (q.get("image") or "").strip()
        if img_file:
            img_path = os.path.join(base_dir, img_file)
            if os.path.exists(img_path):
                st.image(img_path, width=650)  # ← use_column_width 사용 안 함
            else:
                ph = os.path.join(base_dir, "placeholder_light_gray_block.png")
                if os.path.exists(ph):
                    st.image(ph, caption="이미지를 찾을 수 없습니다.", width=650)

        # 입력 폼
        with st.form(key=f"form_q_{q['id']}"):
            if (q.get("type") or "").strip() == "객관식":
                choices = [c for c in (q.get("choices") or []) if c]
                answer = st.radio("정답을 선택하세요:", options=choices, index=None)
            else:
                answer = st.text_input("정답을 입력하세요:", value="")
            submitted = st.form_submit_button("다음")

        if submitted:
            # 객관식 문제에서 답이 선택되지 않았을 때 경고를 표시합니다.
            if (q.get("type") or "").strip() == "객관식" and not answer:
                st.warning("보기를 선택해 주세요.")
                st.stop()
            # 주관식 문제에서 입력이 비어 있을 때 경고를 표시합니다.
            is_blank_subjective = (
                (q.get("type") or "").strip() == "주관식"
                and (answer or "").strip() == ""
            )
            if is_blank_subjective:
                st.warning("정답을 입력해 주세요.")
                st.stop()
            # 답을 기록하고 다음 문제로 넘어갑니다.
            ss.answers[str(q["id"])] = (answer or "").strip()
            ss.page += 1
            st.rerun()
        return

    # 결과 페이지
    if ss.page > total:
        correct = 0
        rows = []
        for q in questions:
            qid = str(q["id"])
            my = ss.answers.get(qid, "")
            ok = judge(my, q.get("answer", ""), q.get("type", ""))
            if ok:
                correct += 1
            rows.append({
                "문항": int(qid), "문제": q.get("question", ""),
                "내 답": my, "정답": q.get("answer", ""), "정오": "O" if ok else "X",
            })

        name = ss.username.strip()
        st.header(f"{name}님의 결과" if name else "결과")

        img_name, msg = result_tier(correct)
        img_path = os.path.join(base_dir, img_name)
        if os.path.exists(img_path):
            st.image(img_path, width=650)  # 결과 이미지도 동일 규칙
        st.success(f"총 {total}문제 중 {correct}개 정답!  {msg}")

        st.markdown("#### 정답/오답 확인")
        st.table(rows)

        if st.button("처음부터 다시 풀기"):
            ss.page = 0
            ss.answers = {}
            st.rerun()

# 스크립트가 직접 실행될 때만 main()을 호출합니다.
if __name__ == "__main__":
    main()