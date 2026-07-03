from service.matching_engine_service import filter_requests_by_concrete, GeoCandidateService, filter_by_quantity


class TestService:

    def __init__(self, db):
        self.db = db

    def run_pipeline(self, request_dict):

        geo_service = GeoCandidateService(self.db)
        geo_service.load_data()

        # radius/w1/w2 נלקחים מברירות המחדל שב-config.py (OD-9)
        candidates = geo_service.get_candidates(
            lat=float(request_dict["lat"]),
            lng=float(request_dict["lng"]),
        )

        candidates = filter_requests_by_concrete(
            concrete_id=request_dict["concrete_id"],
            db=self.db,
            candidates=candidates
        )

        candidates = filter_by_quantity(
            required_quantity=request_dict["quantity"],
            candidates=candidates
        )

        return candidates