import asyncio
import os

import pika
import json
from sqlalchemy.orm import Session
import aio_pika
from app.db.database import SessionLocal
from app.deployments.models import Deployment, DeploymentStatus
from app.clusters.models import Cluster



# async def schedule_deployment(db: Session, deployment_id: int):
#     # Connect to RabbitMQ
#
#     connection = await aio_pika.connect_robust(host='rabbitmq',
#                                                port=5672,
#                                                login='guest',
#                                                password='guest')
#
#     channel = connection.channel()
#
#     # Declare a queue
#     channel.declare_queue(name='deployment_queue')
#
#     channel.publish(
#         exchange='',
#         routing_key='deployment_queue',
#         body=json.dumps({'deployment_id': deployment_id})
#     )

    #
    #
    #
    # await connection.close()





async def schedule_deployment(db: Session, deployment_id: int):
    # Connect to RabbitMQ

    max_retries = 5
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            connection = await aio_pika.connect_robust(
                host=os.getenv('RABBITMQ_HOST', 'localhost'),
                port=int(os.getenv('RABBITMQ_PORT', 5672)),
                login=os.getenv('RABBITMQ_USER', 'guest'),
                password=os.getenv('RABBITMQ_PASSWORD', 'guest')
            )
            return
        except Exception as e:
            print(f"Failed to connect to RabbitMQ (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                print("Max retries reached. Unable to connect to RabbitMQ.")

    async with connection:
        # Creating channel
        channel = await connection.channel()

        # Declaring queue
        queue = await channel.declare_queue('deployment_queue')

        # Publishing message
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps({'deployment_id': deployment_id}).encode()),
            routing_key='deployment_queue'
        )

    print(f"Deployment {deployment_id} scheduled")



async def run_deployment_processor():
    # Connect to RabbitMQ
    max_retries = 5
    retry_delay = 5  # seconds

    for attempt in range(max_retries):
        try:
            connection = await aio_pika.connect_robust(
                host=os.getenv('RABBITMQ_HOST', 'localhost'),
                port=int(os.getenv('RABBITMQ_PORT', 5672)),
                login=os.getenv('RABBITMQ_USER', 'guest'),
                password=os.getenv('RABBITMQ_PASSWORD', 'guest')
            )
            return
        except Exception as e:
            print(f"Failed to connect to RabbitMQ (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                print("Max retries reached. Unable to connect to RabbitMQ.")

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue("deployment_queue")
        async def on_message(message: aio_pika.IncomingMessage):
            async with message.process():
                deployment_data = json.loads(message.body)
                deployment_id = deployment_data["deployment_id"]
                print(f"Processing deployment: {deployment_id}")
                db = SessionLocal()
                try:
                    await process_deployment(db, deployment_id)
                finally:
                    db.close()
        await queue.consume(on_message)
        print("Waiting for deployments. To exit press CTRL+C")

        await asyncio.Future()  # Run forever


async def process_deployment(db: Session, deployment_id: int):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        print(f"Deployment {deployment_id} not found.")
        return

    cluster = db.query(Cluster).filter(Cluster.id == deployment.cluster_id).first()
    if not cluster:
        print(f"Cluster for Deployment {deployment_id} not found.")
        return

    # Get all queued deployments for this cluster, ordered by priority (highest first)
    queued_deployments = db.query(Deployment).filter(
        Deployment.cluster_id == cluster.id,
        Deployment.status == DeploymentStatus.QUEUED
    ).order_by(Deployment.priority.desc()).all()

    # Check if there are higher priority deployments
    higher_priority_exists = any(d.priority > deployment.priority for d in queued_deployments)

    if (cluster.available_ram >= deployment.ram_required and
            cluster.available_cpu >= deployment.cpu_required and
            cluster.available_gpu >= deployment.gpu_required and
            not higher_priority_exists):
        # Allocate resources and start deployment
        cluster.available_ram -= deployment.ram_required
        cluster.available_cpu -= deployment.cpu_required
        cluster.available_gpu -= deployment.gpu_required
        deployment.status = DeploymentStatus.RUNNING
        db.commit()
        print(f"Deployment {deployment_id} (priority: {deployment.priority}) started on cluster {cluster.name}")
    else:
        # Keep in queue if resources are not available or there are higher priority deployments
        deployment.status = DeploymentStatus.QUEUED
        db.commit()
        if higher_priority_exists:
            print(
                f"Deployment {deployment_id} (priority: {deployment.priority}) queued due to higher priority deployments")
        else:
            print(f"Deployment {deployment_id} (priority: {deployment.priority}) queued due to insufficient resources")

