from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from typing import Optional
import uuid

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; background-color: #f8f9fa; }
            .header { background: #343a40; color: white; padding: 1rem; display: flex; justify-content: space-between; align-items: center; }
            .container { max-width: 1200px; margin: 20px auto; padding: 0 20px; }
            .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .metric-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .metric-value { font-size: 2em; font-weight: bold; color: #007bff; }
            .metric-label { color: #666; margin-top: 5px; }
            .btn { background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; }
            .btn:hover { background: #218838; }
            .btn-danger { background: #dc3545; }
            .btn-danger:hover { background: #c82333; }
            #dashboard-data { display: none; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>E-commerce Dashboard</h1>
            <div>
                <a href="/withdraw" class="btn">Withdraw Funds</a>
                <a href="/logout" class="btn btn-danger">Logout</a>
            </div>
        </div>
        
        <div class="container">
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value" id="balance">$0.00</div>
                    <div class="metric-label">Current Balance</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="total-products">0</div>
                    <div class="metric-label">Products Sold</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="total-profit">$0.00</div>
                    <div class="metric-label">Total Profit</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="total-revenue">$0.00</div>
                    <div class="metric-label">Total Revenue</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="total-orders">0</div>
                    <div class="metric-label">Total Orders</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="total-sales">$0.00</div>
                    <div class="metric-label">Total Sales</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="profit-forecast">$0.00</div>
                    <div class="metric-label">Profit Forecast</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="shop-followers">0</div>
                    <div class="metric-label">Shop Followers</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="shop-rating">0.0</div>
                    <div class="metric-label">Shop Rating</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="credit-score">0</div>
                    <div class="metric-label">Credit Score</div>
                </div>
            </div>
        </div>

        <script>
            // Get token from URL
            const urlParams = new URLSearchParams(window.location.search);
            const token = urlParams.get('token');
            
            if (token) {
                // Store token for API calls
                localStorage.setItem('token', token);
                // Remove token from URL
                window.history.replaceState({}, document.title, "/dashboard");
            }
            
            // Load dashboard data
            const storedToken = localStorage.getItem('token');
            if (storedToken) {
                fetch('/api/dashboard', {
                    headers: {
                        'Authorization': 'Bearer ' + storedToken
                    }
                })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('balance').textContent = '$' + data.balance.toFixed(2);
                    document.getElementById('total-products').textContent = data.total_products_sold;
                    document.getElementById('total-profit').textContent = '$' + data.total_profit.toFixed(2);
                    document.getElementById('total-revenue').textContent = '$' + data.total_revenue.toFixed(2);
                    document.getElementById('total-orders').textContent = data.total_orders;
                    document.getElementById('total-sales').textContent = '$' + data.total_sales.toFixed(2);
                    document.getElementById('profit-forecast').textContent = '$' + data.profit_forecast.toFixed(2);
                    document.getElementById('shop-followers').textContent = data.shop_followers;
                    document.getElementById('shop-rating').textContent = data.shop_rating.toFixed(1);
                    document.getElementById('credit-score').textContent = data.credit_score;
                })
                .catch(error => {
                    console.error('Error loading dashboard:', error);
                    window.location.href = '/login';
                });
            } else {
                window.location.href = '/login';
            }
        </script>
    </body>
    </html>
    """

@app.get("/api/dashboard", response_model=DashboardResponse)
async def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    dashboard = db.query(Dashboard).filter(Dashboard.user_id == current_user.id).first()
    if not dashboard:
        # Create dashboard if it doesn't exist
        dashboard = Dashboard(user_id=current_user.id)
        db.add(dashboard)
        db.commit()
        db.refresh(dashboard)
    
    return DashboardResponse(
        balance=dashboard.balance,
        total_products_sold=dashboard.total_products_sold,
        total_profit=dashboard.total_profit,
        total_revenue=dashboard.total_revenue,
        total_orders=dashboard.total_orders,
        total_sales=dashboard.total_sales,
        profit_forecast=dashboard.profit_forecast,
        shop_followers=dashboard.shop_followers,
        shop_rating=dashboard.shop_rating,
        credit_score=dashboard.credit_score
    )
    