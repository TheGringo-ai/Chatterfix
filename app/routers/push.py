"""
Push Notification Router for ChatterFix CMMS
Handles push notification subscriptions and sending
"""

from typing import Optional

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.push_notification_service import push_service

router = APIRouter(prefix="/api/push", tags=["push-notifications"])


class PushSubscription(BaseModel):
    user_id: int
    subscription: dict  # Contains endpoint, keys.p256dh, keys.auth


class NotificationRequest(BaseModel):
    user_id: int
    title: str
    body: str
    url: Optional[str] = "/"
    priority: Optional[str] = "normal"


class BroadcastRequest(BaseModel):
    title: str
    body: str
    url: Optional[str] = "/"
    priority: Optional[str] = "normal"
    user_ids: Optional[list] = None


@router.post("/subscribe")
async def subscribe_push(data: PushSubscription):
    """
    Register a push notification subscription

    The subscription object should contain:
    - endpoint: The push service URL
    - keys.p256dh: The p256dh key
    - keys.auth: The auth key
    """
    try:
        success = push_service.register_subscription(data.user_id, data.subscription)
        if success:
            return JSONResponse(
                content={"success": True, "message": "Push subscription registered"}
            )
        else:
            raise HTTPException(
                status_code=500, detail="Failed to register subscription"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unsubscribe")
async def unsubscribe_push(user_id: int = Body(...)):
    """Unregister push notification subscription"""
    try:
        success = push_service.unregister_subscription(user_id)
        return JSONResponse(
            content={
                "success": success,
                "message": (
                    "Subscription removed" if success else "No subscription found"
                ),
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send")
async def send_notification(request: NotificationRequest):
    """Send a push notification to a specific user"""
    try:
        result = await push_service.send_notification(
            user_id=request.user_id,
            title=request.title,
            body=request.body,
            url=request.url,
            priority=request.priority,
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/broadcast")
async def broadcast_notification(request: BroadcastRequest):
    """Send a notification to all users or a specific list"""
    try:
        results = await push_service.broadcast_notification(
            title=request.title,
            body=request.body,
            url=request.url,
            priority=request.priority,
            user_ids=request.user_ids,
        )
        return JSONResponse(content=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/{user_id}")
async def send_test_notification(user_id: int):
    """Send a test notification to verify push is working"""
    try:
        result = await push_service.send_notification(
            user_id=user_id,
            title="🔔 Test Notification",
            body="Push notifications are working! This is a test from ChatterFix.",
            url="/",
            priority="normal",
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vapid-public-key")
async def get_vapid_public_key():
    """
    Get the VAPID public key for push subscription

    In production, this would return an actual VAPID key.
    For demo purposes, return a placeholder.
    """
    return JSONResponse(
        content={
            "publicKey": "VAPID_PUBLIC_KEY_PLACEHOLDER",
            "note": "Configure VAPID keys in production for Web Push",
        }
    )
