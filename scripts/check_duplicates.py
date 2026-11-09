# scripts/check_duplicates.py
"""
Script de auditoría y saneamiento previo de registros duplicados antes de aplicar
las restricciones de unicidad (UniqueConstraint) en la base de datos:
  1. academic_enrollments -> uq_enrollment_group_student (group_id, student_id)
  2. exam_attempt_answers -> uq_attempt_question (attempt_id, question_id)

Es 100% idempotente: si encuentra filas duplicadas heredadas, conserva el registro
más reciente (mayor id / activo) y sanea los duplicados dentro de una transacción ACID.
"""
import os
import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app import create_app
from app.extensions import db
from app.utils.database import transactional_session


def check_and_clean_duplicates(fix: bool = True) -> dict:
    app = create_app()
    summary = {
        "duplicate_enrollments_found": 0,
        "duplicate_enrollments_cleaned": 0,
        "duplicate_answers_found": 0,
        "duplicate_answers_cleaned": 0,
    }

    with app.app_context():
        print("=" * 75)
        print(" AUDITORÍA Y SANEAMIENTO DE DUPLICADOS PRE-MIGRACIÓN (RAMA 2)")
        print("=" * 75)

        # 1. Auditar duplicados en academic_enrollments (group_id, student_id)
        dup_enroll_sql = text("""
            SELECT group_id, student_id, COUNT(*) AS cnt, MAX(id) AS keep_id
            FROM academic_enrollments
            GROUP BY group_id, student_id
            HAVING COUNT(*) > 1
        """)
        dup_enrollments = db.session.execute(dup_enroll_sql).fetchall()
        summary["duplicate_enrollments_found"] = len(dup_enrollments)
        print(f"[-] Pares (group_id, student_id) duplicados en academic_enrollments: {len(dup_enrollments)}")

        # 2. Auditar duplicados en exam_attempt_answers (attempt_id, question_id)
        dup_ans_sql = text("""
            SELECT attempt_id, question_id, COUNT(*) AS cnt, MAX(id) AS keep_id
            FROM exam_attempt_answers
            GROUP BY attempt_id, question_id
            HAVING COUNT(*) > 1
        """)
        dup_answers = db.session.execute(dup_ans_sql).fetchall()
        summary["duplicate_answers_found"] = len(dup_answers)
        print(f"[-] Pares (attempt_id, question_id) duplicados en exam_attempt_answers: {len(dup_answers)}")

        if fix and (dup_enrollments or dup_answers):
            with transactional_session():
                for row in dup_enrollments:
                    del_res = db.session.execute(
                        text("""
                            DELETE FROM academic_enrollments
                            WHERE group_id = :group_id
                              AND student_id = :student_id
                              AND id <> :keep_id
                        """),
                        {"group_id": row.group_id, "student_id": row.student_id, "keep_id": row.keep_id},
                    )
                    summary["duplicate_enrollments_cleaned"] += del_res.rowcount

                for row in dup_answers:
                    del_res = db.session.execute(
                        text("""
                            DELETE FROM exam_attempt_answers
                            WHERE attempt_id = :attempt_id
                              AND question_id = :question_id
                              AND id <> :keep_id
                        """),
                        {"attempt_id": row.attempt_id, "question_id": row.question_id, "keep_id": row.keep_id},
                    )
                    summary["duplicate_answers_cleaned"] += del_res.rowcount

            print(
                f"[+] Saneamiento completado: "
                f"{summary['duplicate_enrollments_cleaned']} matrículas duplicadas eliminadas, "
                f"{summary['duplicate_answers_cleaned']} respuestas duplicadas eliminadas."
            )
        else:
            print("[OK] Base de datos limpia: 0 duplicados conflictivos.")

    return summary


if __name__ == "__main__":
    check_and_clean_duplicates(fix=True)
