import smartpy as sp

@sp.module
def main():
    operator_permission: type = sp.record(owner=sp.address, operator=sp.address, token_id=sp.nat).layout(("owner", ("operator", "token_id")))
    update_operators_params: type = list[sp.variant(add_operator=operator_permission, remove_operator=operator_permission)]
    tx: type = sp.record(to_=sp.address, token_id=sp.nat, amount=sp.nat).layout(("to_", ("token_id", "amount")))
    transfer_batch: type = sp.record(from_=sp.address, txs=list[tx]).layout(("from_", "txs"))
    transfer_params: type = list[transfer_batch]
    balance_of_request: type = sp.record(owner=sp.address, token_id=sp.nat).layout(("owner", "token_id"))
    balance_of_response: type = sp.record(request=balance_of_request, balance=sp.nat).layout(("request", "balance"))
    balance_of_params: type = sp.record(callback=sp.contract[list[balance_of_response]], requests=list[balance_of_request]).layout(("requests", "callback"))
    mint_params: type = sp.record(owner=sp.address, metadata=sp.map[sp.string, sp.bytes]).layout(("owner", "metadata"))
    is_operator_request: type = sp.record(owner=sp.address, operator=sp.address, token_id=sp.nat).layout(("owner", ("operator", "token_id")))
    token_owners: type = sp.big_map[sp.nat, sp.address]
    token_metadata: type = sp.big_map[sp.nat, sp.map[sp.string, sp.bytes]]

    class TokenContract(sp.Contract):
        def __init__(self, metadata, minter):
            self.data.metadata = sp.cast(metadata, sp.big_map[sp.string, sp.bytes])
            self.data.token_metadata = sp.cast(sp.big_map(), token_metadata)
            self.data.token_owners = sp.cast(sp.big_map(), token_owners);
            self.data.minter = minter
            self.data.next_token_id = 1

        @sp.entrypoint
        def update_operators(self, params):
            sp.cast(params, update_operators_params)

            raise "FA2_OPERATORS_UNSUPPORTED"

        @sp.entrypoint
        def transfer(self, params):
            sp.cast(params, transfer_params)

            raise "FA2_TX_DENIED"

        @sp.entrypoint
        def balance_of(self, params):
            sp.cast(params, balance_of_params)

            responses = []

            for request in params.requests:
                balance = 0

                if self.data.token_metadata.contains(request.token_id) and self.data.token_owners[request.token_id] == request.owner:
                    balance = 1

                responses.push(sp.cast(sp.record(request=request, balance=balance), balance_of_response))

            sp.transfer(responses, sp.mutez(0), params.callback)

        @sp.entrypoint
        def mint(self, params):
            assert sp.sender == self.data.minter, "FA2_NOT_ADMIN"

            sp.cast(params, mint_params)

            self.data.token_owners[self.data.next_token_id] = params.owner
            self.data.token_metadata[self.data.next_token_id] = params.metadata
            self.data.next_token_id += 1

        @sp.offchain_view
        def token_metadata(self, params):
            sp.cast(params, sp.nat)

            assert self.data.token_metadata.contains(params), "FA2_TOKEN_UNDEFINED"

            return self.data.token_metadata[params]

        @sp.offchain_view
        def get_balance(self, params):
            sp.cast(params, balance_of_request)

            assert self.data.token_metadata.contains(params.token_id), "FA2_TOKEN_UNDEFINED"

            balance = 0

            if self.data.token_owners[params.token_id] == params.owner:
                balance = 1

            return balance

        @sp.offchain_view
        def total_supply(self, params):
            sp.cast(params, sp.nat)

            assert self.data.token_metadata.contains(params), "FA2_TOKEN_UNDEFINED"

            return 1

        @sp.offchain_view
        def all_tokens(self):
            list = []

            if self.data.next_token_id > 1:
                list = sp.range(1, self.data.next_token_id)

            return list

        @sp.offchain_view
        def is_operator(self, params):
            sp.cast(params, is_operator_request)

            return False
