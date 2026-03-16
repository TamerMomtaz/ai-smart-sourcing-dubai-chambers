## AUTH RULES — NEVER VIOLATE THESE
1. Auth uses supabase.auth.get_user(token) — NEVER jose.jwt.decode()
2. Auth returns dict with keys: id, email, sub (=id), role
3. Role comes from chamber_users table, NOT from JWT claims
4. Admin must be in EVERY allowed_roles list
5. DO NOT rewrite auth when adding features — import the existing dependency
6. If you need to touch auth, explain WHY before changing anything
## DATABASE RULES
7. ALL tables use chamber_ prefix — verify every .table() call
8. Check constraints exist — query pg_constraint before inserting new values
9. Use keyword arguments for ALL service function calls
9a. submitter_id in chamber_proposals references chamber_vendors(id) — auto-create vendor record if user doesn't have one
## ROUTE RULES
10. Route paths use "" not "/" in FastAPI
11. ALL routes must be registered in main.py — verify before finishing
12. No duplicate route prefixes
13. CORSMiddleware BEFORE routes in main.py
## AI INTERACTION RULES
9b. chamber_ai_interactions.operation_type valid values: evaluation, extraction, classification, summary, trend_analysis, compliance_check, proposal_evaluation
9c. chamber_ai_interactions.user_id references chamber_users(id) — may not match auth user
## DEPLOYMENT RULES
14. Keep both requirements.txt files in sync (root + backend/)
15. Test imports: python -c "from services.gateway import app"
16. Never change working code unless the task requires it
