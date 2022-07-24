from rest_framework import status
from rest_framework.response import Response


class Responses:
    # OK
    user_approved = Response({"detail" : f"user was successfully approved"}, status=status.HTTP_200_OK)

    # Bad request
    no_institute = Response({"detail" : "no institute was provided"}, status=status.HTTP_400_BAD_REQUEST)
    no_pathogen_code = Response({"detail" : "no pathogen_code was provided"}, status=status.HTTP_400_BAD_REQUEST)

    # Forbidden
    different_institute = Response({"detail" : "cannot approve this user. they belong to a different institute"}, status=status.HTTP_403_FORBIDDEN)
    cannot_provide_cid = Response({"detail" : "cids are generated internally and cannot be provided"}, status=status.HTTP_403_FORBIDDEN)
    cannot_be_institute = Response({"detail" : "user cannot create/modify data for this institute"}, status=status.HTTP_403_FORBIDDEN)
    cannot_query_id = Response({"detail" : "cannot query id field"}, status=status.HTTP_403_FORBIDDEN)
