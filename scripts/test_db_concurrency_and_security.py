# scripts/test_db_concurrency_and_security.py
"""
Suite Automatizada de Pruebas — Sprint 2 (Rama 5):
Concurrencia Multihilo, Transacciones ACID, Planes EXPLAIN (Índices SARGables),
Parametrización Explícita (Anti-SQLi), Connection Pooling y Hardening OWASP API.

Diseñada para ser 100% autosuficiente, idempotente y limpia (elimina sus fixtures
temporales 'TMP_CONC_*' en el bloque finally sin alterar datos de demostración).
"""
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text, inspect
from flask_jwt_extended import create_access_token, create_refresh_token
from config import Config
from app import create_app
from app.extensions import db
from app.core_security.models import Person, User, Role, UserHasRole, PasswordResetToken
from app.core_security.services import SecurityService
from app.core_security.repositories import SecurityRepository
from app.core_academic.models import (
    Group, Enrollment, Topic, OVA, Exam, Question, Option, AnswerKey,
    ExamAttempt, AttemptAnswer
)
from app.core_academic.services import AcademicService
from app.utils.decorators import clear_rate_limit_buckets

app = create_app()
results = []


def record_test(test_id: str, module: str, description: str, condition: bool, detail: str = ""):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {test_id} ({module}): {description}")
    if detail:
        print(f"         -> {detail}")
    results.append((test_id, module, description, bool(condition), detail))


def main():
    created_ids = {
        "groups": [],
        "topics": [],
        "ovas": [],
        "exams": [],
        "users": [],
        "persons": [],
    }

    print("\n" + "=" * 88)
    print(" SUITE INTEGRAL DE AUDITORÍA Y CALIDAD: CONCURRENCIA, ACID, EXPLAIN Y OWASP (v2.0)")
    print("=" * 88 + "\n")

    with app.app_context():
        try:
            # ── 1. VERIFICACIÓN DE CONNECTION POOLING ─────────────────────────────
            print("[-] BLOQUE 1: Verificación de Connection Pooling Resiliente (TiDB Cloud / MySQL)")
            pool_opts = Config._build_engine_options("mysql+pymysql://u:p@host:4000/db")
            pool_ok = (
                pool_opts.get("pool_size") == 10
                and pool_opts.get("max_overflow") == 20
                and pool_opts.get("pool_timeout") == 15
                and pool_opts.get("pool_recycle") == 280
                and pool_opts.get("pool_pre_ping") is True
                and pool_opts.get("pool_use_lifo") is True
                and pool_opts.get("connect_args", {}).get("connect_timeout") == 10
            )
            record_test(
                "POOL-01",
                "config.QueuePool",
                "Parámetros de Connection Pooling (size=10, overflow=20, recycle=280s, pre_ping, LIFO)",
                pool_ok,
                f"opts={pool_opts}",
            )

            # ── 2. AUDITORÍA DE ÍNDICES COMPUESTOS Y PLANES EXPLAIN ───────────────
            print("\n[-] BLOQUE 2: Verificación de Índices Compuestos B-Tree y Planes de Ejecución EXPLAIN")
            insp = inspect(db.engine)
            expected_indexes = {
                "persons": "idx_person_email_active",
                "user_has_role": "idx_uhr_user_active",
                "password_reset_tokens": "idx_prt_user_used_expires",
                "academic_groups": "idx_group_teacher_active",
                "academic_enrollments": "idx_enroll_student_group_active",
                "academic_topics": "idx_topic_group_active_order",
                "academic_ovas": "idx_ova_topic_active_order",
                "academic_ova_resources": "idx_resource_ova_active_order",
                "exam_questions": "idx_question_exam_active_order",
                "exam_options": "idx_option_question_active_order",
                "exam_attempts": "idx_attempt_student_exam_active",
                "exam_attempt_answers": "idx_att_ans_attempt_active",
                "academic_group_observers": "idx_observer_user_group_active",
                "student_progress": "idx_progress_ova_user_created",
            }
            missing_idx = []
            for tbl, idx_name in expected_indexes.items():
                names = {i["name"] for i in insp.get_indexes(tbl)}
                if idx_name not in names:
                    missing_idx.append(f"{tbl}.{idx_name}")
            record_test(
                "IDX-01",
                "schema.indexes",
                "Presencia física de los índices compuestos B-Tree en las 14 tablas del esquema",
                len(missing_idx) == 0,
                f"Verificados={len(expected_indexes)}/{len(expected_indexes)}, Faltantes={missing_idx}",
            )

            # Ejecutar EXPLAIN sobre consultas SARGables en MySQL/TiDB
            dialect_name = db.engine.dialect.name
            if dialect_name == "mysql":
                explain_queries = [
                    (
                        "EXP-01",
                        "exam_attempts",
                        "EXPLAIN SELECT COUNT(id) FROM exam_attempts WHERE student_id = 1 AND exam_id = 1 AND is_active = 1",
                        "idx_attempt_student_exam_active",
                    ),
                    (
                        "EXP-02",
                        "academic_enrollments",
                        "EXPLAIN SELECT id, student_id FROM academic_enrollments WHERE group_id = 1 AND is_active = 1",
                        "idx_enroll_group_active",
                    ),
                    (
                        "EXP-03",
                        "academic_topics",
                        "EXPLAIN SELECT id, title FROM academic_topics WHERE group_id = 1 AND is_active = 1 ORDER BY order_index",
                        "idx_topic_group_active_order",
                    ),
                    (
                        "EXP-04",
                        "password_reset_tokens",
                        "EXPLAIN SELECT id FROM password_reset_tokens WHERE user_id = 1 AND is_used = 0 AND expires_at > '2026-01-01 00:00:00'",
                        "idx_prt_user_used_expires",
                    ),
                ]
                for exp_id, tbl_label, sql_str, expected_key in explain_queries:
                    rows = db.session.execute(text(sql_str)).mappings().all()
                    row = rows[0] if rows else {}
                    possible = str(row.get("possible_keys") or "")
                    chosen_key = str(row.get("key") or "")
                    access_type = str(row.get("type") or "")
                    uses_index = (expected_key in chosen_key) or (expected_key in possible)
                    record_test(
                        exp_id,
                        f"EXPLAIN.{tbl_label}",
                        f"Consulta SARGable utiliza índice compuesto '{expected_key}'",
                        uses_index,
                        f"type={access_type}, key={chosen_key}, possible_keys={possible}",
                    )

            # ── 3. PREPARACIÓN DE FIXTURES TEMPORALES ─────────────────────────────
            print("\n[-] Preparando fixtures temporales para pruebas de concurrencia y seguridad...")
            for rname in ("docente", "estudiante", "practicante", "administrador"):
                if not Role.query.filter_by(name=rname).first():
                    SecurityService.create_role(rname, f"Rol {rname}")

            t_owner = SecurityService.register_user(
                "DocConc", "Owner", "9900112233", "tmp_conc_doc1", "Pass#2026!", role_name="docente"
            )
            t_other = SecurityService.register_user(
                "DocConc", "Other", "9900112234", "tmp_conc_doc2", "Pass#2026!", role_name="docente"
            )
            s_main = SecurityService.register_user(
                "EstConc", "Main", "9900112235", "tmp_conc_est1", "Pass#2026!", role_name="estudiante"
            )
            s_enroll = SecurityService.register_user(
                "EstConc", "Enroll", "9900112236", "tmp_conc_est2", "Pass#2026!", role_name="estudiante"
            )
            for u_dict in (t_owner, t_other, s_main, s_enroll):
                created_ids["users"].append(u_dict["id"])
                u_obj = db.session.get(User, u_dict["id"])
                if u_obj:
                    created_ids["persons"].append(u_obj.person_id)

            grp = AcademicService.create_group(t_owner["id"], "TMP_CONC_Grupo_Física")
            created_ids["groups"].append(grp["id"])
            enr_main = AcademicService.create_enrollment(s_main["id"], grp["id"], user_id=t_owner["id"])

            top = AcademicService.create_topic(grp["id"], "TMP_CONC_Tema", user_id=t_owner["id"])
            created_ids["topics"].append(top["id"])
            ova = AcademicService.create_ova(top["id"], "TMP_CONC_OVA", user_id=t_owner["id"])
            created_ids["ovas"].append(ova["id"])

            # Examen con max_attempts = 1 para probar condición de carrera bajo concurrencia
            exam = AcademicService.create_exam(
                ova["id"], "TMP_CONC_Examen_Cupo1", passing_score=60, max_attempts=1, user_id=t_owner["id"]
            )
            created_ids["exams"].append(exam["id"])
            q1 = AcademicService.create_question(exam["id"], "¿F = m * a?", points=10, user_id=t_owner["id"])
            o1_ok = AcademicService.create_option(q1["id"], "Verdadero", user_id=t_owner["id"])
            o1_bad = AcademicService.create_option(q1["id"], "Falso", user_id=t_owner["id"])
            AcademicService.set_answer_key(q1["id"], o1_ok["id"], user_id=t_owner["id"])

            tok_est1 = create_access_token(identity=str(s_main["id"]), additional_claims={"roles": ["estudiante"]})
            tok_est2 = create_access_token(identity=str(s_enroll["id"]), additional_claims={"roles": ["estudiante"]})
            tok_doc1 = create_access_token(identity=str(t_owner["id"]), additional_claims={"roles": ["docente"]})
            tok_doc2 = create_access_token(identity=str(t_other["id"]), additional_claims={"roles": ["docente"]})

            # ── 4. PRUEBAS DE CONCURRENCIA MULTIHILO (SELECT ... FOR UPDATE) ──────
            print("\n[-] BLOQUE 3: Pruebas de Concurrencia Multihilo y Bloqueos Pesimistas (FOR UPDATE)")

            # CT-01: 10 hilos simultáneos intentando iniciar un examen con max_attempts=1
            num_threads = 10
            barrier_start = threading.Barrier(num_threads)

            def worker_start_attempt(_):
                with app.app_context():
                    client = app.test_client()
                    barrier_start.wait()
                    resp = client.post(
                        "/api/v1/academic/attempts",
                        json={"exam_id": exam["id"]},
                        headers={"Authorization": f"Bearer {tok_est1}"},
                    )
                    db.session.remove()
                    return resp.status_code, resp.get_json()

            with ThreadPoolExecutor(max_workers=num_threads) as ex_pool:
                start_outcomes = list(ex_pool.map(worker_start_attempt, range(num_threads)))

            codes_start = [c for c, _ in start_outcomes]
            created_count = codes_start.count(201)
            rejected_count = codes_start.count(400)
            db.session.remove()
            db_attempts = ExamAttempt.query.filter_by(
                student_id=s_main["id"], exam_id=exam["id"], is_active=True
            ).all()
            record_test(
                "CONC-01",
                "AcademicService.start_attempt",
                "10 hilos simultáneos en examen con max_attempts=1 -> exactamente 1 creado (201) y 9 bloqueados (400)",
                created_count == 1 and rejected_count == (num_threads - 1) and len(db_attempts) == 1,
                f"201={created_count}, 400={rejected_count}, filas_en_BD={len(db_attempts)}",
            )

            winning_attempt_id = db_attempts[0].id

            # CT-02: 5 hilos simultáneos enviando respuestas al mismo intento
            num_sub_threads = 5
            barrier_sub = threading.Barrier(num_sub_threads)

            def worker_submit_attempt(_):
                with app.app_context():
                    client = app.test_client()
                    barrier_sub.wait()
                    resp = client.post(
                        f"/api/v1/academic/attempts/{winning_attempt_id}/submit",
                        json={"answers": [{"question_id": q1["id"], "selected_option_id": o1_ok["id"]}]},
                        headers={"Authorization": f"Bearer {tok_est1}"},
                    )
                    db.session.remove()
                    return resp.status_code

            with ThreadPoolExecutor(max_workers=num_sub_threads) as ex_pool:
                sub_codes = list(ex_pool.map(worker_submit_attempt, range(num_sub_threads)))

            sub_200 = sub_codes.count(200)
            sub_400 = sub_codes.count(400)
            db.session.remove()
            ans_count = AttemptAnswer.query.filter_by(attempt_id=winning_attempt_id).count()
            record_test(
                "CONC-02",
                "AcademicService.submit_attempt",
                "5 hilos simultáneos enviando el mismo intento -> exactamente 1 calificado (200) y 4 rechazados (400)",
                sub_200 == 1 and sub_400 == (num_sub_threads - 1) and ans_count == 1,
                f"200={sub_200}, 400={sub_400}, AttemptAnswers_en_BD={ans_count}",
            )

            # CT-03: 5 hilos simultáneos intentando consumir el mismo token de reset_password
            fp_res = SecurityService.forgot_password("tmp_conc_est1")
            raw_reset_tok = fp_res.get("dev_token")
            barrier_rst = threading.Barrier(5)

            def worker_reset_pw(idx):
                with app.app_context():
                    client = app.test_client()
                    barrier_rst.wait()
                    resp = client.post(
                        "/api/v1/security/reset-password",
                        json={"token": raw_reset_tok, "new_password": f"ConcurrPass#{idx}!"},
                    )
                    db.session.remove()
                    return resp.status_code

            with ThreadPoolExecutor(max_workers=5) as ex_pool:
                rst_codes = list(ex_pool.map(worker_reset_pw, range(5)))

            record_test(
                "CONC-03",
                "SecurityService.reset_password",
                "5 hilos simultáneos con el mismo token de recuperación -> exactamente 1 éxito (200) y 4 rechazados (400)",
                rst_codes.count(200) == 1 and rst_codes.count(400) == 4,
                f"200={rst_codes.count(200)}, 400={rst_codes.count(400)}",
            )

            # CT-04: 5 hilos simultáneos matriculando al mismo estudiante en el mismo grupo
            barrier_enr = threading.Barrier(5)

            def worker_enroll(_):
                with app.app_context():
                    client = app.test_client()
                    barrier_enr.wait()
                    resp = client.post(
                        "/api/v1/academic/enrollments",
                        json={"student_id": s_enroll["id"], "group_id": grp["id"]},
                        headers={"Authorization": f"Bearer {tok_doc1}"},
                    )
                    db.session.remove()
                    return resp.status_code

            with ThreadPoolExecutor(max_workers=5) as ex_pool:
                enr_codes = list(ex_pool.map(worker_enroll, range(5)))

            db.session.remove()
            enr_rows = Enrollment.query.filter_by(student_id=s_enroll["id"], group_id=grp["id"]).count()
            record_test(
                "CONC-04",
                "AcademicService.create_enrollment",
                "5 hilos simultáneos matriculando al mismo estudiante -> exactamente 1 creado (201) y 4 rechazados (400)",
                enr_codes.count(201) == 1 and enr_codes.count(400) == 4 and enr_rows == 1,
                f"201={enr_codes.count(201)}, 400={enr_codes.count(400)}, filas_en_BD={enr_rows}",
            )

            # ── 5. TRANSACCIONES ACID, PARAMETRIZACIÓN Y HARDENING OWASP ──────────
            print("\n[-] BLOQUE 4: Atomicidad ACID, Parametrización Anti-SQLi y Hardening OWASP API")

            # ACID-01: Rollback atómico en register_user si falla la asignación de rol
            orig_assign = SecurityRepository.assign_role_to_user

            def fail_assign(*args, **kwargs):
                raise RuntimeError("Fallo simulado de integridad en asignación de rol")

            SecurityRepository.assign_role_to_user = staticmethod(fail_assign)
            try:
                SecurityService.register_user(
                    "Ghost", "Rollback", "9900998877", "ghost_conc_user", "Pass123!", role_name="estudiante"
                )
            except RuntimeError:
                pass
            finally:
                SecurityRepository.assign_role_to_user = orig_assign

            orphan_person = Person.query.filter_by(document_id="9900998877").first()
            orphan_user = User.query.filter_by(username="ghost_conc_user").first()
            record_test(
                "ACID-01",
                "transactional_session",
                "Rollback automático en register_user revierte Person y User cuando falla el paso 3",
                orphan_person is None and orphan_user is None,
                f"orphan_person={orphan_person}, orphan_user={orphan_user}",
            )

            # SQLI-01: Parametrización explícita neutraliza vectores de inyección SQL
            sqli_payload = "' OR '1'='1' -- "
            sqli_blocked = (
                SecurityRepository.is_token_blacklisted(sqli_payload) is False
                and SecurityRepository.get_user_by_identifier(sqli_payload) is None
            )
            record_test(
                "SQLI-01",
                "sqlalchemy.bindparam",
                "Consultas explícitamente parametrizadas neutralizan vectores de inyección SQL",
                sqli_blocked,
                f"payload={sqli_payload!r} -> neutralizado",
            )

            # OWASP-01: Cierre de IDORs en /enrollments/<id> y /students/<id>/attempts
            client = app.test_client()
            r_idor_enr = client.get(
                f"/api/v1/academic/enrollments/{enr_main['id']}",
                headers={"Authorization": f"Bearer {tok_doc2}"},
            )
            r_idor_att = client.get(
                f"/api/v1/academic/students/{s_main['id']}/attempts",
                headers={"Authorization": f"Bearer {tok_doc2}"},
            )
            record_test(
                "OWASP-01",
                "academic.routes",
                "Bloqueo de IDOR horizontal para docentes ajenos en /enrollments/<id> y /students/<id>/attempts",
                r_idor_enr.status_code == 403 and r_idor_att.status_code == 403,
                f"enrollment_status={r_idor_enr.status_code}, attempts_status={r_idor_att.status_code}",
            )

            # OWASP-02: Rate Limiting en /login bloquea ataques de fuerza bruta con HTTP 429
            app.config["ENABLE_RATE_LIMIT_IN_TESTS"] = True
            clear_rate_limit_buckets()
            login_codes = [
                client.post("/api/v1/security/login", json={"username": "tmp_conc_est1", "password": "bad"}).status_code
                for _ in range(12)
            ]
            app.config["ENABLE_RATE_LIMIT_IN_TESTS"] = False
            clear_rate_limit_buckets()
            record_test(
                "OWASP-02",
                "decorators.rate_limit",
                "Rate Limiting por ventana deslizante bloquea ráfagas de fuerza bruta con HTTP 429",
                429 in login_codes,
                f"códigos_obtenidos={login_codes}",
            )

        finally:
            # ── LIMPIEZA GARANTIZADA DE FIXTURES TEMPORALES ───────────────────────
            db.session.rollback()
            for eid in created_ids["exams"]:
                for att in ExamAttempt.query.filter_by(exam_id=eid).all():
                    AttemptAnswer.query.filter_by(attempt_id=att.id).delete()
                    db.session.delete(att)
                for q in Question.query.filter_by(exam_id=eid).all():
                    AnswerKey.query.filter_by(question_id=q.id).delete()
                    Option.query.filter_by(question_id=q.id).delete()
                    db.session.delete(q)
                ex_obj = db.session.get(Exam, eid)
                if ex_obj:
                    db.session.delete(ex_obj)
            for oid in created_ids["ovas"]:
                ova_obj = db.session.get(OVA, oid)
                if ova_obj:
                    db.session.delete(ova_obj)
            for tid in created_ids["topics"]:
                t_obj = db.session.get(Topic, tid)
                if t_obj:
                    db.session.delete(t_obj)
            for gid in created_ids["groups"]:
                Enrollment.query.filter_by(group_id=gid).delete()
                g_obj = db.session.get(Group, gid)
                if g_obj:
                    db.session.delete(g_obj)
            for uid in created_ids["users"]:
                PasswordResetToken.query.filter_by(user_id=uid).delete()
                UserHasRole.query.filter_by(user_id=uid).delete()
                u_obj = db.session.get(User, uid)
                if u_obj:
                    db.session.delete(u_obj)
            for pid in created_ids["persons"]:
                p_obj = db.session.get(Person, pid)
                if p_obj:
                    db.session.delete(p_obj)
            db.session.commit()

    total = len(results)
    passed = sum(1 for _, _, _, ok, _ in results if ok)
    failed = total - passed

    print("\n" + "=" * 88)
    print(f" RESUMEN FINAL: Total ejecutadas: {total} | Exitosas: {passed} | Fallidas: {failed}")
    print("=" * 88)
    if failed > 0:
        sys.exit(1)
    print("\n>>> [100% PASS] AUDITORÍA DE CONCURRENCIA, TRANSACCIONES, EXPLAIN Y SEGURIDAD SUPERADA!\n")


if __name__ == "__main__":
    main()
