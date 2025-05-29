from django.db import connection

def pengunjung_sebagai_adopter(request):
    context = {
        'is_adopter': False
    }

    if not request.session.get('user') or request.session['user'].get('role') != 'pengunjung':
        return context

    username = request.session['user'].get('username')
    if not username:
        return context

    with connection.cursor() as cursor:
        try:
            cursor.execute("""
                SELECT 1 FROM ADOPTER
                WHERE username_adopter = %s
                LIMIT 1
            """, [username])
            
            context['is_adopter'] = cursor.fetchone() is not None
            
        except Exception as e:
            print(f"Error checking adopter status: {e}")
    return context
