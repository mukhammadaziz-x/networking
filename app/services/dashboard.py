from datetime import date, datetime, time, timedelta
from typing import Dict, Any, List, Tuple
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from app.models.company import Company
from app.models.deal import Deal, DealStage
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.task import Task, TaskStatus
from app.models.user import User


def get_dashboard_kpis(db: Session) -> Dict[str, Any]:
    """Calculates all key performance indicators (KPIs) for the dashboard"""
    today = date.today()
    first_day_of_month = datetime(today.year, today.month, 1)
    
    total_companies = db.query(Company).count()
    
    # Open deals are lead, qualified, and proposal stages
    open_stages = [DealStage.LEAD, DealStage.QUALIFIED, DealStage.PROPOSAL]
    open_deals_count = db.query(Deal).filter(Deal.stage.in_(open_stages)).count()
    open_deals_value = db.query(func.coalesce(func.sum(Deal.amount), 0)).filter(
        Deal.stage.in_(open_stages)
    ).scalar()
    
    # Won deals this month
    won_deals_month_count = db.query(Deal).filter(
        Deal.stage == DealStage.WON,
        Deal.created_at >= first_day_of_month
    ).count()
    won_deals_month_value = db.query(func.coalesce(func.sum(Deal.amount), 0)).filter(
        Deal.stage == DealStage.WON,
        Deal.created_at >= first_day_of_month
    ).scalar()
    
    # Total orders and revenue this month (excluding cancelled orders)
    orders_month_count = db.query(Order).filter(
        Order.order_date >= first_day_of_month
    ).count()
    revenue_month_value = db.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(
        Order.status != OrderStatus.CANCELLED,
        Order.order_date >= first_day_of_month
    ).scalar()
    
    # Tasks
    open_tasks = db.query(Task).filter(Task.status.in_([TaskStatus.OPEN, TaskStatus.IN_PROGRESS])).count()
    overdue_tasks = db.query(Task).filter(
        Task.status != TaskStatus.DONE,
        Task.due_date < today
    ).count()
    
    return {
        "total_companies": total_companies,
        "open_deals_count": open_deals_count,
        "open_deals_value": float(open_deals_value),
        "won_deals_month_count": won_deals_month_count,
        "won_deals_month_value": float(won_deals_month_value),
        "orders_month_count": orders_month_count,
        "revenue_month_value": float(revenue_month_value),
        "open_tasks_count": open_tasks,
        "overdue_tasks_count": overdue_tasks
    }


def get_chart_data(db: Session) -> Dict[str, Any]:
    """Generates the datasets required by Chart.js graphs"""
    today = date.today()
    
    # 1. Sales revenue by month (last 6 months)
    start_date = datetime(today.year, today.month, 1) - timedelta(days=150)
    start_date = datetime(start_date.year, start_date.month, 1)
    
    orders = db.query(Order).filter(
        Order.status != OrderStatus.CANCELLED,
        Order.order_date >= start_date
    ).all()
    
    monthly_map = {}
    curr_year, curr_month = start_date.year, start_date.month
    for _ in range(6):
        m_key = f"{curr_year}-{curr_month:02d}"
        monthly_map[m_key] = 0.0
        curr_month += 1
        if curr_month > 12:
            curr_month = 1
            curr_year += 1
            
    for order in orders:
        m_key = order.order_date.strftime("%Y-%m")
        if m_key in monthly_map:
            monthly_map[m_key] += float(order.total_amount)
            
    sales_labels = []
    sales_values = []
    curr_year, curr_month = start_date.year, start_date.month
    for _ in range(6):
        m_key = f"{curr_year}-{curr_month:02d}"
        sales_labels.append(datetime(curr_year, curr_month, 1).strftime("%b %Y"))
        sales_values.append(monthly_map[m_key])
        curr_month += 1
        if curr_month > 12:
            curr_month = 1
            curr_year += 1
            
    # 2. Deals by Stage
    deal_counts = {stage.value: 0 for stage in DealStage}
    deal_values = {stage.value: 0.0 for stage in DealStage}
    deals = db.query(Deal).all()
    for deal in deals:
        stage_val = deal.stage.value
        deal_counts[stage_val] += 1
        deal_values[stage_val] += float(deal.amount)
        
    deal_labels = [stage.value.capitalize() for stage in DealStage]
    deal_count_data = [deal_counts[stage.value] for stage in DealStage]
    deal_value_data = [deal_values[stage.value] for stage in DealStage]
    
    # 3. Orders by Status
    order_counts = {status.value: 0 for status in OrderStatus}
    db_order_counts = db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    for status_obj, count in db_order_counts:
        order_counts[status_obj.value] = count
        
    order_labels = [status.value.capitalize() for status in OrderStatus]
    order_values = [order_counts[status.value] for status in OrderStatus]
    
    # 4. Top 5 Products by Quantity sold
    top_products = db.query(
        Product.name,
        func.sum(OrderItem.quantity).label("total_qty")
    ).join(OrderItem).join(Order).filter(
        Order.status != OrderStatus.CANCELLED
    ).group_by(Product.id, Product.name).order_by(
        desc("total_qty")
    ).limit(5).all()
    
    product_labels = [p[0] for p in top_products]
    product_values = [int(p[1]) for p in top_products]
    
    return {
        "sales_revenue": {
            "labels": sales_labels,
            "data": sales_values
        },
        "deals_by_stage": {
            "labels": deal_labels,
            "counts": deal_count_data,
            "values": deal_value_data
        },
        "orders_by_status": {
            "labels": order_labels,
            "data": order_values
        },
        "top_products": {
            "labels": product_labels,
            "data": product_values
        }
    }


def get_sales_report_data(db: Session, start_date: date, end_date: date) -> Dict[str, Any]:
    """Retrieves order lists, revenue aggregates, and counts in a date range"""
    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date, time.max)
    
    orders = db.query(Order).filter(
        Order.order_date >= start_dt,
        Order.order_date <= end_dt
    ).order_by(Order.order_date.desc()).all()
    
    revenue = sum(float(o.total_amount) for o in orders if o.status != OrderStatus.CANCELLED)
    order_count = len(orders)
    
    return {
        "orders": orders,
        "revenue": revenue,
        "order_count": order_count,
        "start_date": start_date,
        "end_date": end_date
    }


def get_pipeline_report_data(db: Session) -> Dict[str, Any]:
    """Retrieves deal value summaries grouped by Stage and Owner"""
    # 1. By Stage
    stage_data = db.query(
        Deal.stage,
        func.count(Deal.id),
        func.sum(Deal.amount)
    ).group_by(Deal.stage).all()
    
    stage_report = []
    for stage_enum, count, val in stage_data:
        stage_report.append({
            "stage": stage_enum.value.capitalize(),
            "count": count,
            "value": float(val or 0)
        })
        
    # 2. By Owner
    owner_data = db.query(
        User.name,
        func.count(Deal.id),
        func.sum(Deal.amount)
    ).join(Deal, Deal.owner_id == User.id).group_by(User.id, User.name).all()
    
    owner_report = []
    for name, count, val in owner_data:
        owner_report.append({
            "owner": name,
            "count": count,
            "value": float(val or 0)
        })
        
    return {
        "by_stage": stage_report,
        "by_owner": owner_report
    }
