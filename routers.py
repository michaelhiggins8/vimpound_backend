from routes.vapi_webhook.vapi_webhook import router as vapi_webhook_router
from routes.phone_number_routes.create_free_vapi_phone_number import router as create_free_vapi_phone_number_router
from routes.phone_number_routes.change_free_vapi_phone_number import router as change_free_vapi_phone_number_router
from routes.phone_number_routes.get_vapi_phone_number_from_database import router as get_vapi_phone_number_from_database_router
from routes.orgs_routes.change_agent_name import router as change_agent_name_router
from routes.orgs_routes.change_company_name import router as change_company_name_router
from routes.orgs_routes.change_default_address import router as change_default_address_router
from routes.orgs_routes.change_time_zone import router as change_time_zone_router
from routes.orgs_routes.change_default_hours import router as change_default_hours_router
from routes.orgs_routes.exception_dates_routes.get_exception_dates import router as get_exception_dates_router
from routes.orgs_routes.exception_dates_routes.create_exception_date import router as create_exception_date_router
from routes.orgs_routes.exception_dates_routes.delete_exception_date import router as delete_exception_date_router
from routes.orgs_routes.exception_dates_routes.update_exception_date import router as update_exception_date_router
from routes.orgs_routes.items_needed_routes.get_items_needed import router as get_items_needed_router
from routes.orgs_routes.items_needed_routes.change_items_needed import router as change_documents_needed_router
from routes.orgs_routes.auction_triggers_routes.change_auction_triggers import router as change_auction_triggers_router
from routes.orgs_routes.get_orgs_content import router as get_orgs_content_router
from routes.orgs_routes.get_orgs_content_by_phone import router as get_orgs_content_by_phone_router
from routes.orgs_routes.costs_routes.change_extra_costs import router as change_cost_to_release_long_router
from routes.orgs_routes.costs_routes.change_main_costs import router as change_cost_to_release_short_router
from routes.orgs_routes.costs_routes.get_customer_portal import router as get_customer_portal_router
from routes.aux_routes.make_user import router as make_user_router
from routes.aux_routes.SubscribeURL import router as subscribe_url_router
from routes.aux_routes.check_if_subscribed import router as check_if_subscribed_router
import importlib.util
import sys
import os
vehicle_pagination_path = os.path.join(os.path.dirname(__file__), 'routes', 'vehicle_routes.py', 'vehicle_pagination.py')
spec = importlib.util.spec_from_file_location("vehicle_pagination", vehicle_pagination_path)
vehicle_pagination_module = importlib.util.module_from_spec(spec)
sys.modules["vehicle_pagination"] = vehicle_pagination_module
spec.loader.exec_module(vehicle_pagination_module)
vehicle_pagination_router = vehicle_pagination_module.router

add_vehicle_path = os.path.join(os.path.dirname(__file__), 'routes', 'vehicle_routes.py', 'add_vehicle.py')
spec = importlib.util.spec_from_file_location("add_vehicle", add_vehicle_path)
add_vehicle_module = importlib.util.module_from_spec(spec)
sys.modules["add_vehicle"] = add_vehicle_module
spec.loader.exec_module(add_vehicle_module)
add_vehicle_router = add_vehicle_module.router

delete_vehicle_path = os.path.join(os.path.dirname(__file__), 'routes', 'vehicle_routes.py', 'delete_vehicle.py')
spec = importlib.util.spec_from_file_location("delete_vehicle", delete_vehicle_path)
delete_vehicle_module = importlib.util.module_from_spec(spec)
sys.modules["delete_vehicle"] = delete_vehicle_module
spec.loader.exec_module(delete_vehicle_module)
delete_vehicle_router = delete_vehicle_module.router

get_addresses_path = os.path.join(os.path.dirname(__file__), 'routes', 'vehicle_routes.py', 'get_addresses.py')
spec = importlib.util.spec_from_file_location("get_addresses", get_addresses_path)
get_addresses_module = importlib.util.module_from_spec(spec)
sys.modules["get_addresses"] = get_addresses_module
spec.loader.exec_module(get_addresses_module)
get_addresses_router = get_addresses_module.router

add_address_path = os.path.join(os.path.dirname(__file__), 'routes', 'vehicle_routes.py', 'add_address.py')
spec = importlib.util.spec_from_file_location("add_address", add_address_path)
add_address_module = importlib.util.module_from_spec(spec)
sys.modules["add_address"] = add_address_module
spec.loader.exec_module(add_address_module)
add_address_router = add_address_module.router

delete_address_path = os.path.join(os.path.dirname(__file__), 'routes', 'vehicle_routes.py', 'delete_address.py')
spec = importlib.util.spec_from_file_location("delete_address", delete_address_path)
delete_address_module = importlib.util.module_from_spec(spec)
sys.modules["delete_address"] = delete_address_module
spec.loader.exec_module(delete_address_module)
delete_address_router = delete_address_module.router

routers=[vapi_webhook_router, create_free_vapi_phone_number_router, change_free_vapi_phone_number_router, get_vapi_phone_number_from_database_router, change_agent_name_router, change_company_name_router, change_default_address_router, change_time_zone_router, change_default_hours_router, get_exception_dates_router, create_exception_date_router, delete_exception_date_router, update_exception_date_router, get_items_needed_router, change_documents_needed_router, change_auction_triggers_router, get_orgs_content_router, get_orgs_content_by_phone_router, change_cost_to_release_long_router, change_cost_to_release_short_router, get_customer_portal_router, vehicle_pagination_router, add_vehicle_router, delete_vehicle_router, get_addresses_router, add_address_router, delete_address_router, make_user_router, subscribe_url_router, check_if_subscribed_router]