from typing import Any
import random
from hashlib import sha256
import pytz
from datetime import datetime, timedelta
from util import supabase

"""
Operations:
register post
login get
machine-access get
events get (list events), post (add event)
submissions get (list submissions), delete (reject a submission)
"""

def now(): return datetime.now(pytz.utc)

def apply_salt(password: str, salt: str): return salt[:len(salt) // 2] + password + salt[len(salt) // 2:]

def register(method: str, body: Any):
    """
        [
            email,
            password,
            name,
            first_name,
            last_name,
            machine_id
        ]
    """
    salt = (lambda: ''.join(random.choices('abcdefghijkmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ123456780!@#$%^&*()~`_-+={}[]|\\:";\'<>,.?/', k=32)) + ''.join(random.choices('abcdefghijkmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ123456780!@#$%^&*()~`_-+={}[]|\\:";\'<>,.?/', k=random.randint(1, 32))))()
    
    if method != 'POST':
        return 'invalid method', 403
    
    res = supabase.table('companies').insert({
        'company_name': body.get('name').strip(),
        'company_email': body.get('email').strip(),
        'verified': False,
        'hashed_password': sha256(apply_salt(body.get('password').strip(), salt).encode()).hexdigest(),
        'salt': salt,
        'first_name': body.get('first_name').strip(),
        'last_name': body.get('last_name').strip(),
    }).execute()
    
    if hasattr(res, 'code'):
        return 'error', 501
    
    res = supabase.table('company_machines').upsert({
        'machine_id': body.get('machine_id').strip(),
        'company_id': res.data[0]['company_id'],
        'valid_until': (now() + timedelta(days=1)).isoformat()
    }).execute()
    
    if hasattr(res, 'code'):
        return 'error', 501
    
    return {
        'access_code': res.data[0]['access_code'],
        'id': res.data[0]['company_id'],
        'email': body.get('email').strip(),
        'name': body.get('name').strip(),
    }, 200
    
def machine_access(method: str, body: Any):
    """
        [
            machine_id,
            access_code,
        ]
    """
    if method != 'PUT': 
        return 'invalid method', 403
    
    res = supabase.table('company_machines').select(
        'company_id,'
        'access_code,'
        'companies (company_name, company_email)'
    )
    if body.get('access_code') is not None:
        res = res.eq('access_code', body.get('access_code')).gt('valid_until', now().isoformat())
    else:
        res = res.eq('machine_id', body.get('machine_id')).gt('valid_until', now().isoformat())
        
    res = res.execute()
    if hasattr(res, 'code'):
        return 'error', 501
    if len(res.data) == 0:
        return 'invalid access', 404

    return {
        'access_code': res.data[0]['access_code'],
        'id': res.data[0]['company_id'],
        'name': res.data[0]['companies']['company_name'],
        'email': res.data[0]['companies']['company_email'],
    }, 200
    
def login(method: str, body: Any):
    """
        [
            machine_id?,
            access_code?, // either or OR
            
            email!,
            password!,
        ]
    """
    if method != 'PUT':
        return 'invalid method', 403
    
    print(body)
    if (body.get('machine_id') is None and body.get('access_code') is None) and (body.get('email') is None or body.get('password') is None):
        return 'invalid body', 400
    
    if body.get('access_code') is not None:
        return machine_access('PUT', { 'access_code': body.get('access_code') })
    
    if body.get('machine_id') is not None and (body.get('email') is None or body.get('password') is None):
        return machine_access('PUT', { 'machine_id': body.get('machine_id') })
    
    res = supabase.table('companies').select('company_id, hashed_password, company_email, company_name, salt').eq('company_email', body.get('email')).execute()
    if hasattr(res, 'code'):
        return 'error', 501
    if len(res.data) == 0:
        return 'invalid creds', 404
        
    email, name = None, None
    for company in res.data:
        if company['hashed_password'] != sha256(apply_salt(body.get('password'), res.data[0]['salt']).encode()).hexdigest():
            return 'invalid creds', 404
        email, name = company['company_email'], company['company_name']
    
    res = supabase.table('company_machines').upsert({
        'machine_id': body.get('machine_id').strip(),
        'company_id': res.data[0]['company_id'],
        'valid_until': (now() + timedelta(days=1)).isoformat()
    }).execute()
    
    if hasattr(res, 'code'):
        return 'error', 501
    
    result = {
        'access_code': res.data[0]['access_code'],
        'id': res.data[0]['company_id'],
        'email': email,
        'name': name,
    }, 200
    
    res = supabase.table('companies').update({ 'last_login': now().isoformat() }).eq('company_id', result[0]['id']).execute()
    return result
    
def signout(method: str, body: Any):
    """
        [
            machine_id?, 
            access_code?, // either or OR
        ]
    """
    if method != 'PUT':
        return 'invalid method', 400
    
    res = supabase.table('company_machines').delete()
    if body.get('access_code') is not None:
        res = res.eq('access_code', body.get('access_code'))
    else:
        res = res.eq('machine_id', body.get('machine_id'))
    res = res.execute()
    
    if hasattr(res, 'code'):
        return 'error', 501
    return 'Signed out', 200
    
def events(method: str, body: Any):
    """
        [
            access_code,
            id,
            
            (post?)
            event_id?, // for updates
            event_name,
            start_time?,
            end_time?,
            short_description,
            long_description,
            prize,
        ]
    """
    
    result = machine_access('PUT', { 'access_code': body.get('access_code') })
    if result[1] != 200 or result[0].get('id') != body.get('id'):
        return 'invalid token', 400
    
    def put():
        res = supabase.table('events').select(', '.join('*'.split())).eq('company_id', body.get('id')).execute()
        if hasattr(res, 'code'):
            return 'error', 501
        return res.data, 200
        
    def post():
        res = supabase.table('events')
        if body.get('event_id') is not None:
            res = res.upsert({
                'event_id': body.get('event_id'),
                **({'event_name': body.get('event_name')} if body.get('event_name') is not None else {}),
                **({'start_time': body.get('start_time')} if body.get('start_time') is not None else {}),
                **({'end_time': body.get('end_time')} if body.get('end_time') is not None else {}),
                **({'short_description': body.get('short_description')} if body.get('short_description') is not None else {}),
                **({'long_description': body.get('long_description')} if body.get('long_description') is not None else {}),
                **({'prize': body.get('prize')} if body.get('prize') is not None else {}),
            }).execute()
        else:
            res = res.insert({
                'event_name': body.get('event_name'),
                'company_id': body.get('id'),
                **({'start_time': body.get('start_time')} if body.get('start_time') is not None else {}),
                **({'end_time': body.get('end_time')} if body.get('end_time') is not None else {}),
                'short_description': body.get('short_description'),
                'long_description': body.get('long_description'),
                'prize': body.get('prize'),
            }).execute()
            
        if hasattr(res, 'code'):
            return 'error', 501
        return res.data[0], 200
    
    if method == 'PUT':
        return put()
    if method == 'POST':
        return post()
    return 'invalid method', 403

def submissions(method: str, body: Any):
    """
        [
            access_code,
            id,
            event_id,
            
            (post?)
            submission_id?, // for deletion
        ]
    """
    
    result = machine_access('PUT', { 'access_code': body.get('access_code') })
    if result[1] != 200 or result[0].get('id') != body.get('id'):
        return 'invalid token', 400
    
    def put():
        res = (
            supabase
            .from_("submissions")
            .select(
                '*,'
                'events!inner(event_id, event_name, company_id)'
            )
            .eq('events.event_id', body.get('event_id'))
            .eq("events.company_id", body.get('id'))
            .execute()
        )
        if hasattr(res, 'code'):
            return 'error', 501
        return res.data, 200
    
    def delete():
        if body.get('submission_id') is None:
            return 'cannot delete submission without its id', 400
        res = supabase.table('submissions').delete().eq('submission_id', body.get('submission_id')).execute()
        if hasattr(res, 'code'):
            return 'error', 501
        return res.data[0], 200
    
    if method == 'PUT':
        return put()
    if method == 'DELETE':
        return delete()
    return 'invalid method', 403

def companies(method: str, body: Any):
    """
        [
            access_code,
            id,
            
            first_name?,
            last_name?,
            company_name?,
            email?,
            password?,
            verified?,
        ]
    """
    
    if method != 'POST':
        return 'invalid method', 403
    
    salt = (lambda: ''.join(random.choices('abcdefghijkmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ123456780!@#$%^&*()~`_-+={}[]|\\:";\'<>,.?/', k=32)) + ''.join(random.choices('abcdefghijkmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ123456780!@#$%^&*()~`_-+={}[]|\\:";\'<>,.?/', k=random.randint(1, 32))))()
    
    result = machine_access('PUT', { 'access_code': body.get('access_code') })
    if result[1] != 200 or result[0].get('id') != body.get('id'):
        return 'invalid token', 400
    
    res = supabase.table('companies').update(
        **({ 'first_name': body.get('first_name') } if body.get('first_name') is not None else {})
        **({ 'last_name': body.get('last_name') } if body.get('last_name') is not None else {})
        **({ 'company_name': body.get('company_name') } if body.get('company_name') is not None else {})
        **({ 'hashed_password': sha256(apply_salt(body.get('password').strip(), salt).encode()).hexdigest(), 'salt': salt } if body.get('password') is not None else {})
        **({ 'company_email': body.get('email') } if body.get('email') is not None else {})
        **({ 'verified': body.get('verified') } if body.get('verified') is not None else {})
    ).execute()
    if hasattr(res, 'code'):
        return 'error', 501
    return res.data, 200