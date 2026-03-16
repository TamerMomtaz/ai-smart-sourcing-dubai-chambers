from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY

# Service-role client for privileged DB operations (table reads/writes).
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Anon-key client used ONLY for auth token validation (supabase_auth.auth.get_user).
# The service-role client cannot properly validate user bearer tokens.
supabase_auth = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
