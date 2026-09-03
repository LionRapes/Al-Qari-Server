import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from app.interfaces import YdbInterface
from app.dependencies import get_ydb
from app.utils import ensure_str, get_current_user, get_optional_current_user

router = APIRouter(prefix="/playlists", tags=["Playlists"])


class PlaylistCreate(BaseModel):
    title: str
    data: str
    is_public: bool = False

class PlaylistUpdate(BaseModel):
    title: Optional[str] = None
    data: Optional[str] = None
    is_public: Optional[bool] = None

class ShareLinkCreate(BaseModel):
    role: str
    expires_in_hours: int = 24


@router.post("/", summary="Create a new playlist", status_code=status.HTTP_201_CREATED)
async def create_playlist(
    playlist: PlaylistCreate, 
    user_id: str = Depends(get_current_user),
    db: YdbInterface = Depends(get_ydb)
):
    playlist_id = str(uuid.uuid4())
    query = """
    DECLARE $id AS Utf8;
    DECLARE $owner_id AS Utf8;
    DECLARE $title AS Utf8;
    DECLARE $data AS Utf8;
    DECLARE $is_public AS Bool;
    
    INSERT INTO playlists (id, owner_id, title, data, is_public, created_at, updated_at) 
    VALUES ($id, $owner_id, $title, $data, $is_public, CurrentUtcTimestamp(), CurrentUtcTimestamp());
    """
    db.execute(query, {
        "$id": playlist_id,
        "$owner_id": user_id,
        "$title": playlist.title,
        "$data": playlist.data,
        "$is_public": playlist.is_public
    })
    return {"playlist_id": playlist_id, "message": "Playlist created"}


@router.get("/public", summary="Get paginated list of public playlists")
async def get_public_playlists(
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: YdbInterface = Depends(get_ydb)
):
    query = """
    DECLARE $limit AS Uint64;
    DECLARE $offset AS Uint64;

    SELECT id, owner_id, title, data, is_public, forked_from_id, created_at, updated_at
    FROM playlists
    WHERE is_public = true
    ORDER BY created_at DESC
    LIMIT $limit OFFSET $offset;
    """
    result = db.execute(query, {
        "$limit": limit,
        "$offset": offset
    })

    playlists = []
    if result:
        for row in result:
            playlists.append({
                "id": ensure_str(row["id"]),
                "owner_id": ensure_str(row["owner_id"]),
                "title": ensure_str(row["title"]),
                "data": ensure_str(row["data"]),
                "is_public": row["is_public"],
                "forked_from_id": ensure_str(row.get("forked_from_id", "")),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })

    return {
        "limit": limit,
        "offset": offset,
        "playlists": playlists
    }
from fastapi import APIRouter, Query, Depends
# ... your other imports ...

@router.get("/search", summary="Search public playlists by title")
async def search_public_playlists(
    q: str = Query(..., min_length=1, max_length=100, description="Search keyword"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results to return"),
    db: YdbInterface = Depends(get_ydb)
):
    words = list(set(word.strip() for word in q.split() if word.strip()))[:10]

    if not words:
        return {"query": q, "limit": limit, "playlists": []}

    declare_statements = ["DECLARE $limit AS Uint64;"]
    where_conditions = ["is_public = true"]
    params = {"$limit": limit}

    for i, word in enumerate(words):
        param_name = f"$word_{i}"
        declare_statements.append(f"DECLARE {param_name} AS Utf8;")
        
        where_conditions.append(f"title ILIKE {param_name}")
        params[param_name] = f"%{word}%"

    query = f"""
    {chr(10).join(declare_statements)}

    SELECT id, owner_id, title, data, is_public, forked_from_id, created_at, updated_at
    FROM playlists
    WHERE {" AND ".join(where_conditions)}
    ORDER BY created_at DESC
    LIMIT $limit;
    """

    result = db.execute(query, params)

    playlists = []
    if result:
        for row in result:
            playlists.append({
                "id": ensure_str(row["id"]),
                "owner_id": ensure_str(row["owner_id"]),
                "title": ensure_str(row["title"]),
                "data": ensure_str(row["data"]),
                "is_public": row["is_public"],
                "forked_from_id": ensure_str(row.get("forked_from_id", "")),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })

    return {
        "query": q,
        "limit": limit,
        "playlists": playlists
    }

@router.get("/{playlist_id}", summary="Get a playlist by ID")
async def get_playlist(
    playlist_id: str, 
    current_user_id: Optional[str] = Depends(get_optional_current_user),
    db: YdbInterface = Depends(get_ydb)
):
    query = """
    DECLARE $id AS Utf8;
    SELECT id, owner_id, title, data, is_public, forked_from_id, created_at, updated_at 
    FROM playlists WHERE id = $id;
    """
    result = db.execute(query, {"$id": playlist_id})
    if not result:
        raise HTTPException(status_code=404, detail="Playlist not found")

    playlist = result[0]
    is_public = playlist["is_public"]
    owner_id = ensure_str(playlist["owner_id"])

    if not is_public:
        if not current_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for private playlists",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if current_user_id != owner_id:
            member_query = """
            DECLARE $playlist_id AS Utf8;
            DECLARE $user_id AS Utf8;
            SELECT role FROM playlist_members 
            WHERE playlist_id = $playlist_id AND user_id = $user_id;
            """
            member_result = db.execute(member_query, {
                "$playlist_id": playlist_id,
                "$user_id": current_user_id
            })

            if not member_result:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Access denied to this private playlist"
                )

    return {
        "id": ensure_str(playlist["id"]),
        "owner_id": owner_id,
        "title": ensure_str(playlist["title"]),
        "data": ensure_str(playlist["data"]),
        "is_public": is_public,
        "forked_from_id": ensure_str(playlist.get("forked_from_id", "")),
        "created_at": playlist["created_at"],
        "updated_at": playlist["updated_at"]
    }
    

@router.patch("/{playlist_id}", summary="Update a playlist")
async def update_playlist(
    playlist_id: str, 
    updates: PlaylistUpdate, 
    current_user_id: str = Depends(get_current_user),
    db: YdbInterface = Depends(get_ydb)
):
    fetch_query = "DECLARE $id AS Utf8; SELECT owner_id, title, data, is_public FROM playlists WHERE id = $id;"
    existing = db.execute(fetch_query, {"$id": playlist_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    current = existing[0]
    owner_id = ensure_str(current["owner_id"])

    if current_user_id != owner_id:
        member_query = """
        DECLARE $playlist_id AS Utf8;
        DECLARE $user_id AS Utf8;
        SELECT role FROM playlist_members 
        WHERE playlist_id = $playlist_id AND user_id = $user_id;
        """
        member_result = db.execute(member_query, {
            "$playlist_id": playlist_id,
            "$user_id": current_user_id
        })

        if not member_result:
            raise HTTPException(status_code=403, detail="Access denied")
            
        role = ensure_str(member_result[0]["role"])
        if role != "editor":
            raise HTTPException(status_code=403, detail="Only owners or editors can update this playlist")

    new_title = updates.title if updates.title is not None else ensure_str(current["title"])
    new_data = updates.data if updates.data is not None else ensure_str(current["data"])
    new_is_public = updates.is_public if updates.is_public is not None else current["is_public"]

    update_query = """
    DECLARE $id AS Utf8;
    DECLARE $title AS Utf8;
    DECLARE $data AS Utf8;
    DECLARE $is_public AS Bool;
    
    UPDATE playlists SET 
        title = $title, 
        data = $data, 
        is_public = $is_public, 
        updated_at = CurrentUtcTimestamp() 
    WHERE id = $id;
    """
    db.execute(update_query, {
        "$id": playlist_id,
        "$title": new_title,
        "$data": new_data,
        "$is_public": new_is_public
    })
    return {"message": "Playlist updated successfully"}


@router.delete("/{playlist_id}", summary="Delete a playlist", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playlist(
    playlist_id: str, 
    current_user_id: str = Depends(get_current_user),
    db: YdbInterface = Depends(get_ydb)
):
    check_query = "DECLARE $id AS Utf8; SELECT owner_id FROM playlists WHERE id = $id;"
    result = db.execute(check_query, {"$id": playlist_id})
    if not result:
        raise HTTPException(status_code=404, detail="Playlist not found")
        
    owner_id = ensure_str(result[0]["owner_id"])
    
    if current_user_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only the playlist owner can delete it"
        )

    delete_query = "DECLARE $id AS Utf8; DELETE FROM playlists WHERE id = $id;"
    db.execute(delete_query, {"$id": playlist_id})
    return None


@router.post("/{playlist_id}/fork", summary="Fork a playlist")
async def fork_playlist(
    playlist_id: str, 
    current_user_id: str = Depends(get_current_user),
    db: YdbInterface = Depends(get_ydb)
):
    fetch_query = "DECLARE $id AS Utf8; SELECT title, data, is_public FROM playlists WHERE id = $id;"
    existing = db.execute(fetch_query, {"$id": playlist_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Source playlist not found")
    
    original = existing[0]

    new_id = str(uuid.uuid4())
    
    insert_query = """
    DECLARE $id AS Utf8; DECLARE $owner_id AS Utf8; DECLARE $title AS Utf8;
    DECLARE $data AS Utf8; DECLARE $is_public AS Bool; DECLARE $forked_from AS Utf8;
    
    INSERT INTO playlists (id, owner_id, title, data, is_public, forked_from_id, created_at, updated_at) 
    VALUES ($id, $owner_id, $title, $data, $is_public, $forked_from, CurrentUtcTimestamp(), CurrentUtcTimestamp());
    """
    db.execute(insert_query, {
        "$id": new_id,
        "$owner_id": current_user_id,
        "$title": f"Copy of {ensure_str(original['title'])}",
        "$data": ensure_str(original["data"]),
        "$is_public": False,
        "$forked_from": playlist_id
    })
    return {"new_playlist_id": new_id, "message": "Playlist forked"}


@router.post("/{playlist_id}/share", summary="Generate a shareable link")
async def share_playlist(
    playlist_id: str, 
    req: ShareLinkCreate, 
    current_user_id: str = Depends(get_current_user),
    db: YdbInterface = Depends(get_ydb)
):
    check_owner_query = """
    DECLARE $id AS Utf8;
    SELECT owner_id FROM playlists WHERE id = $id;
    """
    playlist_result = db.execute(check_owner_query, {"$id": playlist_id})

    if not playlist_result:
        raise HTTPException(status_code=404, detail="Playlist not found")

    owner_id = ensure_str(playlist_result[0]["owner_id"])

    if current_user_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the playlist owner can generate shareable links"
        )

    token = str(uuid.uuid4())
    query = f"""
    DECLARE $token AS Utf8;
    DECLARE $playlist_id AS Utf8;
    DECLARE $role AS Utf8;
    
    INSERT INTO playlist_share_links (token, playlist_id, role, expires_at, created_at) 
    VALUES ($token, $playlist_id, $role, CurrentUtcTimestamp() + Interval("PT{req.expires_in_hours}H"), CurrentUtcTimestamp());
    """
    db.execute(query, {
        "$token": token,
        "$playlist_id": playlist_id,
        "$role": req.role
    })
    return {"share_token": token, "expires_in_hours": req.expires_in_hours}


@router.post("/join/{token}", summary="Join a playlist via share token")
async def join_playlist_via_token(
    token: str, 
    user_id: str = Depends(get_current_user), 
    db: YdbInterface = Depends(get_ydb)
):
    verify_query = """
    DECLARE $token AS Utf8;
    SELECT playlist_id, role FROM playlist_share_links 
    WHERE token = $token AND expires_at > CurrentUtcTimestamp();
    """
    token_result = db.execute(verify_query, {"$token": token})
    
    if not token_result:
        raise HTTPException(status_code=400, detail="Invalid or expired invite link")
        
    playlist_id = ensure_str(token_result[0]["playlist_id"])
    token_role = ensure_str(token_result[0]["role"])
    
    check_member_query = """
    DECLARE $playlist_id AS Utf8;
    DECLARE $user_id AS Utf8;
    SELECT role FROM playlist_members 
    WHERE playlist_id = $playlist_id AND user_id = $user_id;
    """
    existing_member = db.execute(check_member_query, {
        "$playlist_id": playlist_id, 
        "$user_id": user_id
    })
    
    if existing_member:
        current_role = ensure_str(existing_member[0]["role"])
        
        if current_role == token_role:
            return {
                "message": "You are already a member of this playlist with this role", 
                "playlist_id": playlist_id,
                "role": current_role
            }
            
        update_role_query = """
        DECLARE $playlist_id AS Utf8;
        DECLARE $user_id AS Utf8;
        DECLARE $new_role AS Utf8;
        
        UPDATE playlist_members 
        SET role = $new_role 
        WHERE playlist_id = $playlist_id AND user_id = $user_id;
        """
        db.execute(update_role_query, {
            "$playlist_id": playlist_id,
            "$user_id": user_id,
            "$new_role": token_role
        })
        
        return {
            "message": f"Your role was updated from {current_role} to {token_role}", 
            "playlist_id": playlist_id, 
            "role": token_role
        }

    insert_member_query = """
    DECLARE $playlist_id AS Utf8;
    DECLARE $user_id AS Utf8;
    DECLARE $role AS Utf8;
    
    INSERT INTO playlist_members (playlist_id, user_id, role, added_at) 
    VALUES ($playlist_id, $user_id, $role, CurrentUtcTimestamp());
    """
    db.execute(insert_member_query, {
        "$playlist_id": playlist_id,
        "$user_id": user_id,
        "$role": token_role
    })
    
    
    delete_token_query = "DECLARE $token AS Utf8; DELETE FROM playlist_share_links WHERE token = $token;"
    db.execute(delete_token_query, {"$token": token})
    
    return {
        "message": "Successfully joined the playlist", 
        "playlist_id": playlist_id, 
        "role": token_role
    }
    
    
@router.get("/{playlist_id}/members", summary="Get all members of a playlist")
async def get_playlist_members(
    playlist_id: str, 
    db: YdbInterface = Depends(get_ydb)
):
    query = """
    DECLARE $playlist_id AS Utf8;
    SELECT m.user_id, m.role, m.added_at, u.username, u.avatar_url
    FROM playlist_members AS m
    LEFT JOIN users AS u ON m.user_id = u.id
    WHERE m.playlist_id = $playlist_id;
    """
    result = db.execute(query, {"$playlist_id": playlist_id})
    
    members = []
    if result:
        for row in result:
            members.append({
                "user_id": ensure_str(row["user_id"]),
                "role": ensure_str(row["role"]),
                "username": ensure_str(row.get("username", "")),
                "avatar_url": ensure_str(row.get("avatar_url", "")),
                "added_at": row["added_at"]
            })
            
    return {"playlist_id": playlist_id, "members": members}


@router.get("/{playlist_id}/members/{user_id}", summary="Get user's relation to a playlist")
async def get_playlist_relation(
    playlist_id: str,
    user_id: str,
    db: YdbInterface = Depends(get_ydb)
):
    owner_query = "DECLARE $id AS Utf8; SELECT owner_id FROM playlists WHERE id = $id;"
    owner_result = db.execute(owner_query, {"$id": playlist_id})
    
    if owner_result and ensure_str(owner_result[0]["owner_id"]) == user_id:
        return {"playlist_id": playlist_id, "user_id": user_id, "role": "owner"}

    member_query = """
    DECLARE $playlist_id AS Utf8;
    DECLARE $user_id AS Utf8;
    SELECT role, added_at FROM playlist_members 
    WHERE playlist_id = $playlist_id AND user_id = $user_id;
    """
    member_result = db.execute(member_query, {
        "$playlist_id": playlist_id,
        "$user_id": user_id
    })
    
    if not member_result:
        raise HTTPException(status_code=404, detail="User has no relation to this playlist")
        
    return {
        "playlist_id": playlist_id,
        "user_id": user_id,
        "role": ensure_str(member_result[0]["role"]),
        "added_at": member_result[0]["added_at"]
    }


@router.get("/user/{user_id}/shared", summary="Get all playlists shared with a user")
async def get_user_shared_playlists(
    user_id: str,
    db: YdbInterface = Depends(get_ydb)
):
    query = """
    DECLARE $user_id AS Utf8;
    SELECT 
        p.id AS playlist_id,
        p.title AS title,
        p.is_public AS is_public,
        m.role AS role,
        m.added_at AS added_at
    FROM playlist_members AS m
    INNER JOIN playlists AS p ON m.playlist_id = p.id
    WHERE m.user_id = $user_id;
    """
    result = db.execute(query, {"$user_id": user_id})
    
    playlists = []
    if result:
        for row in result:
            playlists.append({
                "playlist_id": ensure_str(row["playlist_id"]),
                "title": ensure_str(row["title"]),
                "is_public": row["is_public"],
                "role": ensure_str(row["role"]),
                "added_at": row["added_at"]
            })
            
    return {"user_id": user_id, "playlists": playlists}


@router.get("/user/{user_id}/owned", summary="Get all playlists owned by a user")
async def get_user_owned_playlists(
    user_id: str,
    db: YdbInterface = Depends(get_ydb)
):
    query = """
    DECLARE $user_id AS Utf8;
    SELECT id, title, data, is_public, forked_from_id, created_at, updated_at 
    FROM playlists 
    WHERE owner_id = $user_id;
    """
    result = db.execute(query, {"$user_id": user_id})
    
    playlists = []
    if result:
        for row in result:
            playlists.append({
                "id": ensure_str(row["id"]),
                "title": ensure_str(row["title"]),
                "data": ensure_str(row["data"]),
                "is_public": row["is_public"],
                "forked_from_id": ensure_str(row.get("forked_from_id", "")),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
            
    return {"user_id": user_id, "playlists": playlists}


@router.delete("/{playlist_id}/members/{target_user_id}", summary="Remove a member from a playlist")
async def remove_playlist_member(
    playlist_id: str,
    target_user_id: str,
    current_user_id: str = Depends(get_current_user),
    db: YdbInterface = Depends(get_ydb)
):
    check_owner_query = """
    DECLARE $id AS Utf8;
    SELECT owner_id FROM playlists WHERE id = $id;
    """
    playlist_result = db.execute(check_owner_query, {"$id": playlist_id})

    if not playlist_result:
        raise HTTPException(status_code=404, detail="Playlist not found")

    owner_id = ensure_str(playlist_result[0]["owner_id"])

    if current_user_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the playlist owner can remove members"
        )

    delete_query = """
    DECLARE $playlist_id AS Utf8;
    DECLARE $user_id AS Utf8;
    DELETE FROM playlist_members 
    WHERE playlist_id = $playlist_id AND user_id = $user_id;
    """
    db.execute(delete_query, {
        "$playlist_id": playlist_id,
        "$user_id": target_user_id
    })

    return {"message": f"User {target_user_id} successfully removed from the playlist"}