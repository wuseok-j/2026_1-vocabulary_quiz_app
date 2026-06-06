from __future__ import annotations

import random
import tkinter as tk

from tkinter import ttk, font

from vocabulary_quiz_app.quiz_logic import Word, check_answer, draw_word


class VocabularyQuizApp:
    def __init__(self, root: tk.Tk, words: list[Word]) -> None:
        """단어장 퀴즈 앱의 메인 UI 및 내부 상태를 초기화합니다."""
        self.words = words
        self.rng = random.Random()
        self.current: Word | None = None
        self.checked = False
        
        # 점수 및 퀴즈 진행 상태
        self.score = 0
        self.total = 0
        
        # 학습 기록 저장을 위한 리스트 (단어, 입력, 정답 뜻, 정답 여부, 복습 모드 여부)
        self.history = []
        
        # 오답 관리 (틀린 단어 누적 및 복습 모드용 큐)
        self.incorrect_words: list[Word] = []
        self.review_words: list[Word] = []
        self.is_review_mode = False


        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(family="NanumGothic", size=12)

        root.title("Vocabulary Quiz")
        root.geometry("440x320")
        root.resizable(False, False)

        self.word_var = tk.StringVar(value="단어를 불러오는 중...")
        self.feedback_var = tk.StringVar(value="")
        self.score_var = tk.StringVar(value="Score: 0/0")

        ttk.Label(root, text="영단어").pack(pady=(16, 4))
        ttk.Label(root, textvariable=self.word_var, font=("NanumGothic", 24)).pack()

        self.answer_entry = ttk.Entry(root, font=("NanumGothic", 14))
        self.answer_entry.pack(pady=12, ipadx=6, ipady=4)

        buttons = ttk.Frame(root)
        buttons.pack(pady=6)
        self.check_button = ttk.Button(buttons, text="채점", command=self.check_current)
        self.check_button.pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text="다음", command=self.next_word).pack(
            side=tk.LEFT, padx=6
        )

        ttk.Label(root, textvariable=self.feedback_var).pack(pady=8)
        ttk.Label(root, textvariable=self.score_var).pack()

        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=4)
        ttk.Button(btn_frame, text="통계 보기", command=self.show_statistics).pack(side=tk.LEFT, padx=4)
        
        self.review_btn_text = tk.StringVar(value="오답 복습")
        ttk.Button(btn_frame, textvariable=self.review_btn_text, command=self.toggle_review).pack(side=tk.LEFT, padx=4)
        
        ttk.Button(btn_frame, text="단어 관리", command=self.open_word_management).pack(side=tk.LEFT, padx=4)

        self.next_word()

    def next_word(self, keep_feedback: bool = False) -> None:
        """다음 단어를 무작위로 뽑아 화면에 표시합니다.
        복습 모드일 경우 오답 목록(review_words)에서만 단어를 뽑습니다."""
        # 현재 모드에 따라 출제할 단어 풀(pool)을 결정
        active_pool = self.review_words if self.is_review_mode else self.words
        
        if not active_pool:
            # 복습할 단어가 더 이상 없으면 일반 모드로 자동 복귀
            if self.is_review_mode:
                self.is_review_mode = False
                self.review_btn_text.set("오답 복습")
                self.score = 0
                self.total = 0
                self.score_var.set("Score: 0/0")
                self.feedback_var.set("모든 오답을 복습했습니다! 일반 모드로 돌아왔습니다.")
                self.next_word(keep_feedback=True)
            else:
                self.word_var.set("단어가 없습니다.")
            return

        self.current = draw_word(active_pool, self.rng)
        self.word_var.set(self.current.term)
        self.answer_entry.delete(0, tk.END)
        if not keep_feedback:
            self.feedback_var.set("")
        self.checked = False
        self.check_button.state(["!disabled"])
        self.answer_entry.focus()

    def check_current(self) -> None:
        """사용자가 입력한 답안을 채점하고, 결과에 따라 점수와 오답 목록을 갱신합니다."""
        if self.current is None or self.checked:
            return
        self.checked = True
        self.total += 1
        user_input = self.answer_entry.get()
        is_correct = check_answer(self.current, user_input)
        
        # 채점 결과를 학습 기록에 추가
        self.history.append((self.current.term, user_input, self.current.meaning, is_correct, self.is_review_mode))
        
        if is_correct:
            self.score += 1
            self.feedback_var.set("정답입니다!")
            # 복습 모드에서 정답을 맞추면 복습 및 오답 목록에서 제거하여 완전히 마스터했음을 표시
            if self.is_review_mode and self.current in self.review_words:
                self.review_words.remove(self.current)
                if self.current in self.incorrect_words:
                    self.incorrect_words.remove(self.current)
        else:
            # 일반 모드에서 틀렸을 경우에만 오답 목록에 추가 (중복 방지)
            if not self.is_review_mode and self.current not in self.incorrect_words:
                self.incorrect_words.append(self.current)
            self.feedback_var.set(f"오답입니다. 정답: {self.current.meaning}")
        self.score_var.set(f"Score: {self.score}/{self.total}")
        self.check_button.state(["disabled"])

    def show_statistics(self) -> None:
        """지금까지의 학습 통계(정답률, 모드별 성과 등)와 전체 풀이 기록을 새 창에 보여줍니다."""
        stat_window = tk.Toplevel()
        stat_window.title("학습 통계")
        stat_window.geometry("480x350")
        stat_window.resizable(False, False)
        
        normal_total = normal_score = 0
        review_total = review_score = 0
        
        for term, u_input, mean, is_corr, is_rev in self.history:
            if is_rev:
                review_total += 1
                if is_corr: review_score += 1
            else:
                normal_total += 1
                if is_corr: normal_score += 1
                
        normal_acc = (normal_score / normal_total * 100) if normal_total > 0 else 0.0
        review_acc = (review_score / review_total * 100) if review_total > 0 else 0.0
        
        summary_text = (
            f"[일반 모드] 시도: {normal_total}회 | 정답: {normal_score}회 | 정답률: {normal_acc:.1f}%\n"
            f"[오답 복습] 시도: {review_total}회 | 정답: {review_score}회 | 정답률: {review_acc:.1f}%"
        )
        ttk.Label(stat_window, text=summary_text, font=("NanumGothic", 10, "bold"), justify=tk.CENTER).pack(pady=10)
        
        columns = ("mode", "term", "input", "correct")
        tree = ttk.Treeview(stat_window, columns=columns, show="headings", height=8)
        tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        tree.heading("mode", text="모드")
        tree.heading("term", text="단어")
        tree.heading("input", text="내 입력")
        tree.heading("correct", text="결과")
        
        tree.column("mode", width=60, anchor=tk.CENTER)
        tree.column("term", width=120, anchor=tk.CENTER)
        tree.column("input", width=120, anchor=tk.CENTER)
        tree.column("correct", width=60, anchor=tk.CENTER)
        
        for term, user_input, meaning, is_correct, is_review in reversed(self.history):
            mode_str = "복습" if is_review else "일반"
            result_str = "O" if is_correct else "X"
            tree.insert("", tk.END, values=(mode_str, term, user_input, result_str))

    def toggle_review(self) -> None:
        """일반 모드와 오답 복습 모드를 전환합니다."""
        if self.is_review_mode:
            # 복습 모드 -> 일반 모드로 돌아갈 때 상태 초기화
            self.is_review_mode = False
            self.review_btn_text.set("오답 복습")
            self.score = 0
            self.total = 0
            self.score_var.set("Score: 0/0")
            self.feedback_var.set("일반 모드로 돌아왔습니다.")
            self.next_word(keep_feedback=True)
        else:
            if not self.incorrect_words:
                self.feedback_var.set("복습할 오답이 없습니다.")
                return
            
            # 일반 모드 -> 복습 모드 진입 시 오답 목록을 복습 큐(review_words)로 복사
            self.is_review_mode = True
            self.review_words = list(self.incorrect_words)
            self.review_btn_text.set("일반 모드로 돌아가기")
            self.score = 0
            self.total = 0
            self.score_var.set("Score: 0/0")
            self.feedback_var.set("오답 복습을 시작합니다. 정답 시 목록에서 사라집니다.")
            self.next_word(keep_feedback=True)

    def open_word_management(self) -> None:
        """현재 등록된 단어 목록을 조회하고, 새로운 단어를 추가하거나 기존 단어를 삭제하는 창을 엽니다."""
        manage_window = tk.Toplevel()
        manage_window.title("단어 관리")
        manage_window.geometry("400x400")
        manage_window.resizable(False, False)

        columns = ("term", "meaning")
        tree = ttk.Treeview(manage_window, columns=columns, show="headings", height=10)
        tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        tree.heading("term", text="단어")
        tree.heading("meaning", text="뜻")
        tree.column("term", width=180, anchor=tk.CENTER)
        tree.column("meaning", width=180, anchor=tk.CENTER)

        def refresh_tree():
            for item in tree.get_children():
                tree.delete(item)
            for w in self.words:
                tree.insert("", tk.END, values=(w.term, w.meaning))

        refresh_tree()

        input_frame = ttk.Frame(manage_window)
        input_frame.pack(pady=10)

        ttk.Label(input_frame, text="단어:").grid(row=0, column=0, padx=5)
        term_entry = ttk.Entry(input_frame, width=12)
        term_entry.grid(row=0, column=1, padx=5)

        ttk.Label(input_frame, text="뜻:").grid(row=0, column=2, padx=5)
        meaning_entry = ttk.Entry(input_frame, width=12)
        meaning_entry.grid(row=0, column=3, padx=5)

        def add_word():
            t = term_entry.get().strip()
            m = meaning_entry.get().strip()
            if t and m:
                self.words.append(Word(term=t, meaning=m))
                refresh_tree()
                term_entry.delete(0, tk.END)
                meaning_entry.delete(0, tk.END)

        ttk.Button(input_frame, text="추가", command=add_word).grid(row=0, column=4, padx=5)

        def delete_word():
            selected = tree.selection()
            if not selected:
                return
            item = tree.item(selected[0])
            t, m = item["values"]
            for i, w in enumerate(self.words):
                if w.term == t and w.meaning == m:
                    del self.words[i]
                    if w in self.incorrect_words:
                        self.incorrect_words.remove(w)
                    if w in self.review_words:
                        self.review_words.remove(w)
                    break
            refresh_tree()

        ttk.Button(manage_window, text="선택 삭제", command=delete_word).pack(pady=5)
