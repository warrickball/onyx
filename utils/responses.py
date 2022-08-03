from rest_framework import status
from rest_framework.response import Response


class Responses:
    # OK
    _200_user_approved = Response({"detail" : f"user was successfully approved"}, status=status.HTTP_200_OK)

    # Bad request
    _400_no_institute = Response({"detail" : "no institute was provided"}, status=status.HTTP_400_BAD_REQUEST)
    _400_cannot_provide_cid = Response({"detail" : "cids are generated internally and are not provided in the request"}, status=status.HTTP_400_BAD_REQUEST)
    _400_mismatch_pathogen_code = Response({"detail" : "pathogen_code provided in request body does not match pathogen code in url"}, status=status.HTTP_400_BAD_REQUEST)
    _400_no_updates_provided = Response({"detail" : "no fields to update were provided"}, status=status.HTTP_400_BAD_REQUEST)

    # Forbidden
    _403_different_institute = Response({"detail" : "cannot approve this user. they belong to a different institute"}, status=status.HTTP_403_FORBIDDEN)
    _403_incorrect_institute_for_user = Response({"detail" : "user cannot create/modify data for this institute"}, status=status.HTTP_403_FORBIDDEN)
    _403_cannot_query_id = Response({"detail" : "id fields cannot be queried"}, status=status.HTTP_403_FORBIDDEN)
