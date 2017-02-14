
wasp_debug_angular_app = angular.module('wasp-launcher::wasp-debug', []);

wasp_debug_angular_app.controller('wasp-launcher::wasp-debug::debug-controller', ['$scope', function($scope){

	$scope.request_details = false;
	$scope.route_details = false;
	$scope.response_details = false;

	$scope.exceptions_global_details = false;
	$scope.exceptions_details = [];
}])
