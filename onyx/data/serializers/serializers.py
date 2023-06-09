from rest_framework import serializers
from data.models import Record
from utils.serializers import OnyxSerializer
from utils.validation import (
    enforce_optional_value_groups_create,
    enforce_optional_value_groups_update,
    enforce_yearmonth_order_create,
    enforce_yearmonth_order_update,
    enforce_yearmonth_non_future,
)


class RecordSerializer(OnyxSerializer):
    class Meta:
        model = Record
        fields = [
            "created",
            "last_modified",
            "suppressed",
            "user",
            "site",
            "cid",
            "published_date",
        ]

    def validate(self, data):
        """
        Additional validation carried out on either object creation or update
        """
        model = self.Meta.model
        errors = {}

        # Object update validation
        if self.instance:
            enforce_optional_value_groups_update(
                errors=errors,
                instance=self.instance,
                data=data,
                groups=model.ExtraMeta.optional_value_groups,
            )
            for (
                lower_yearmonth,
                higher_yearmonth,
            ) in model.ExtraMeta.yearmonth_orderings:
                enforce_yearmonth_order_update(
                    errors=errors,
                    instance=self.instance,
                    lower_yearmonth=lower_yearmonth,
                    higher_yearmonth=higher_yearmonth,
                    data=data,
                )
        # Object create validation
        else:
            enforce_optional_value_groups_create(
                errors=errors,
                data=data,
                groups=model.ExtraMeta.optional_value_groups,
            )
            for (
                lower_yearmonth,
                higher_yearmonth,
            ) in model.ExtraMeta.yearmonth_orderings:
                enforce_yearmonth_order_create(
                    errors=errors,
                    lower_yearmonth=lower_yearmonth,
                    higher_yearmonth=higher_yearmonth,
                    data=data,
                )
        # Object create and update validation
        for yearmonth in model.ExtraMeta.yearmonths:
            if data.get(yearmonth):
                enforce_yearmonth_non_future(
                    errors=errors,
                    name=yearmonth,
                    value=data[yearmonth],
                )

        if errors:
            raise serializers.ValidationError(errors)

        return data
