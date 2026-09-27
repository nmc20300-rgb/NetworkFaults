import hashlib
import secrets

from database import (
    get_connection,
    write_audit_log,
)


# ============================================================
# إعدادات الأمان
# ============================================================

PBKDF2_ITERATIONS = 200000


# ============================================================
# Password Hashing
# ============================================================

def hash_password(password, salt=None):
    """
    إنشاء Hash لكلمة المرور باستخدام:
        PBKDF2-HMAC-SHA256

    النتيجة:
        salt$hash
    """

    if password is None:
        password = ""

    password = str(password)

    if salt is None:
        salt = secrets.token_hex(16)

    password_bytes = password.encode("utf-8")
    salt_bytes = salt.encode("utf-8")

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt_bytes,
        PBKDF2_ITERATIONS,
    ).hex()

    return f"{salt}${password_hash}"


def verify_password(password, stored_hash):
    """
    التحقق من كلمة المرور المخزنة.

    stored_hash:
        salt$hash

    يرجع:
        True  -> كلمة المرور صحيحة
        False -> كلمة المرور خاطئة
    """

    if password is None:
        return False

    if not stored_hash:
        return False

    try:
        salt, expected_hash = str(stored_hash).split("$", 1)
    except ValueError:
        return False

    if not salt or not expected_hash:
        return False

    password_bytes = str(password).encode("utf-8")
    salt_bytes = salt.encode("utf-8")

    actual_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt_bytes,
        PBKDF2_ITERATIONS,
    ).hex()

    # مقارنة آمنة ضد timing attacks
    return secrets.compare_digest(
        actual_hash,
        expected_hash,
    )


# ============================================================
# Authentication
# ============================================================

def authenticate(username, password):
    """
    التحقق من بيانات تسجيل الدخول.

    يرجع Dictionary يحتوي بيانات المستخدم
    أو None إذا كان الدخول غير صحيح.

    ملاحظة:
    الصلاحيات يتم تحميلها لاحقًا بواسطة:
        get_user_permissions()
    """

    username = (username or "").strip()

    if not username or not password:
        return None

    connection = get_connection()

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                u.id,
                u.username,
                u.password_hash,
                u.full_name,
                u.role_id,
                u.is_active,
                r.role_code,
                r.role_name
            FROM dbo.users u
            INNER JOIN dbo.roles r
                ON r.id = u.role_id
            WHERE u.username = ?
              AND u.is_active = 1
              AND r.is_active = 1
            """,
            (username,),
        )

        row = cursor.fetchone()

        # المستخدم غير موجود
        if row is None:
            return None

        # كلمة المرور غير صحيحة
        if not verify_password(
            password,
            row["password_hash"],
        ):
            return None

        # ----------------------------------------------------
        # تحديث آخر دخول
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE dbo.users
            SET last_login = SYSDATETIME()
            WHERE id = ?
            """,
            (row["id"],),
        )

        connection.commit()

        # ----------------------------------------------------
        # بيانات المستخدم
        # ----------------------------------------------------

        role_code = str(
            row["role_code"] or ""
        ).strip().upper()

        user = {
            "id": row["id"],
            "username": row["username"],
            "full_name": row["full_name"],
            "role_id": row["role_id"],
            "role_code": role_code,
            "role_name": row["role_name"],
            "is_active": bool(row["is_active"]),
        }

        # ----------------------------------------------------
        # تحميل الصلاحيات
        # ----------------------------------------------------

        user["permissions"] = get_user_permissions(
            row["id"],
            row["role_id"],
        )

        # ----------------------------------------------------
        # Audit Log - Login
        # ----------------------------------------------------

        write_audit_log(
            user=user,
            action="دخول",
            module_name="النظام",
            description="تم تسجيل الدخول بنجاح",
        )

        return user

    except Exception:
        try:
            connection.rollback()
        except Exception:
            pass

        raise

    finally:
        try:
            if cursor is not None:
                cursor.close()
        except Exception:
            pass

        connection.close()


# ============================================================
# User Permissions
# ============================================================

def get_user_permissions(user_id, role_id):
    """
    تحميل صلاحيات المستخدم.

    مصدر الصلاحيات الأساسي:
        role_permissions

    ويمكن لاحقًا إضافة صلاحيات فردية من:
        user_permissions

    SUPER_ADMIN:
        يحصل على كل الصلاحيات تلقائيًا.
    """

    connection = get_connection()

    cursor = None

    try:
        cursor = connection.cursor()

        # ----------------------------------------------------
        # SUPER ADMIN
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT role_code
            FROM dbo.roles
            WHERE id = ?
            """,
            (role_id,),
        )

        role_row = cursor.fetchone()

        role_code = ""

        if role_row:
            role_code = str(
                role_row["role_code"] or ""
            ).strip().upper()

        # ----------------------------------------------------
        # تحميل جميع الصلاحيات الموجودة بالنظام
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                permission_code
            FROM dbo.permissions
            WHERE is_active = 1
            ORDER BY id
            """
        )

        all_permissions = [
            str(row["permission_code"]).strip()
            for row in cursor.fetchall()
            if row["permission_code"]
        ]

        # ----------------------------------------------------
        # SUPER ADMIN = كل الصلاحيات
        # ----------------------------------------------------

        if role_code == "SUPER_ADMIN":
            return {
                permission: True
                for permission in all_permissions
            }

        # ----------------------------------------------------
        # صلاحيات الـ Role
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                p.permission_code,
                rp.allowed
            FROM dbo.role_permissions rp
            INNER JOIN dbo.permissions p
                ON p.id = rp.permission_id
            WHERE rp.role_id = ?
              AND p.is_active = 1
            """,
            (role_id,),
        )

        permissions = {}

        for row in cursor.fetchall():
            permission_code = str(
                row["permission_code"] or ""
            ).strip()

            if permission_code:
                permissions[permission_code] = bool(
                    row["allowed"]
                )

        # ----------------------------------------------------
        # ضمان وجود كل الصلاحيات في Dictionary
        # ----------------------------------------------------

        for permission in all_permissions:
            if permission not in permissions:
                permissions[permission] = False

        # ----------------------------------------------------
        # User-specific permissions
        # ----------------------------------------------------

        try:
            cursor.execute(
                """
                SELECT
                    p.permission_code,
                    up.allowed
                FROM dbo.user_permissions up
                INNER JOIN dbo.permissions p
                    ON p.id = up.permission_id
                WHERE up.user_id = ?
                  AND p.is_active = 1
                """,
                (user_id,),
            )

            for row in cursor.fetchall():
                permission_code = str(
                    row["permission_code"] or ""
                ).strip()

                if permission_code:
                    permissions[permission_code] = bool(
                        row["allowed"]
                    )

        except Exception:
            # user_permissions لن يمنع تسجيل الدخول
            # إذا لم يكن مجهزًا بالكامل بعد.
            pass

        return permissions

    finally:
        try:
            if cursor is not None:
                cursor.close()
        except Exception:
            pass

        connection.close()


# ============================================================
# Permission Helper
# ============================================================

def has_permission(user, permission_code):
    """
    فحص صلاحية معينة للمستخدم.

    مثال:

        if has_permission(user, "devices.edit"):
            ...

    SUPER_ADMIN:
        True دائمًا.
    """

    if not user:
        return False

    role_code = str(
        user.get("role_code", "")
    ).strip().upper()

    # SUPER ADMIN له كل الصلاحيات
    if role_code == "SUPER_ADMIN":
        return True

    permissions = user.get(
        "permissions",
        {},
    )

    if not isinstance(permissions, dict):
        return False

    return bool(
        permissions.get(
            permission_code,
            False,
        )
    )


# ============================================================
# Load / Refresh User Permissions
# ============================================================

def refresh_user_permissions(user):
    """
    إعادة تحميل صلاحيات المستخدم من قاعدة البيانات.

    مفيدة لو تم تعديل صلاحيات المستخدم أثناء تشغيل البرنامج.
    """

    if not user:
        return user

    user["permissions"] = get_user_permissions(
        user.get("id"),
        user.get("role_id"),
    )

    return user


# ============================================================
# Change Password
# ============================================================

def change_password(user_id, new_password):
    """
    تغيير كلمة مرور مستخدم.

    يرجع:
        True  -> تم التغيير
        False -> لم يتم التغيير
    """

    if not user_id:
        return False

    if new_password is None:
        return False

    new_password = str(new_password)

    if not new_password:
        return False

    password_hash = hash_password(
        new_password
    )

    connection = get_connection()

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE dbo.users
            SET password_hash = ?
            WHERE id = ?
            """,
            (
                password_hash,
                user_id,
            ),
        )

        affected = cursor.rowcount

        connection.commit()

        return affected > 0

    except Exception:
        try:
            connection.rollback()
        except Exception:
            pass

        raise

    finally:
        try:
            if cursor is not None:
                cursor.close()
        except Exception:
            pass

        connection.close()


# ============================================================
# Activate / Deactivate User
# ============================================================

def set_user_active(user_id, active):
    """
    تفعيل أو تعطيل مستخدم.

    active:
        True  -> تفعيل
        False -> تعطيل
    """

    if not user_id:
        return False

    connection = get_connection()

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE dbo.users
            SET is_active = ?
            WHERE id = ?
            """,
            (
                1 if active else 0,
                user_id,
            ),
        )

        affected = cursor.rowcount

        connection.commit()

        return affected > 0

    except Exception:
        try:
            connection.rollback()
        except Exception:
            pass

        raise

    finally:
        try:
            if cursor is not None:
                cursor.close()
        except Exception:
            pass

        connection.close()