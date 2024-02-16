import { TezosToolkit } from "@taquito/taquito";
import { tzip16, Tzip16Module } from "@taquito/tzip16";
import { InMemorySigner } from "@taquito/signer";
import { char2Bytes } from '@taquito/utils';

import code from "../artifacts/code.json" assert { type: "json" };
import storage from "../artifacts/storage.json" assert { type: "json" };

const MNEMONIC = "MNEMONIC GOES HERE";

function pack(string) {
    const bytes = char2Bytes(string);
    const bytesLength = (bytes.length / 2).toString(16);
    const addPadding = `00000000${bytesLength}`;
    const paddedBytesLength = addPadding.slice(addPadding.length - 8);
    return "05" + "01" + paddedBytesLength + bytes;
}

const Tezos = new TezosToolkit("https://rpc.ghostnet.teztnets.com");
Tezos.addExtension(new Tzip16Module());

const signer = InMemorySigner.fromMnemonic({mnemonic: MNEMONIC});

Tezos.setSignerProvider(signer);

const address = await signer.publicKeyHash();

console.log(`Account address: ${address}`);
console.log(`Account balance: ${(await Tezos.tz.getBalance(address)).toString()}`);

console.log("Originating contract…");

const origination = await Tezos.contract.originate({
    code: code,
    init: storage
});

console.log(`Contract address: ${origination.contractAddress}`);
console.log("Awaiting confirmation…");

await origination.confirmation();

const contract = await Tezos.contract.at(origination.contractAddress, tzip16);
const tokens = [
    {"owner": "tz1NbEC653mQc1M8GhmAkNdqBogF2wFzGWEw", "metadata": {"decimals": pack("0"), "key1": pack("baab"), "key2": pack("eeee")}},
    {"owner": "tz1NbEC653mQc1M8GhmAkNdqBogF2wFzGWEw", "metadata": {"decimals": pack("0"), "key1": pack("abba"), "key2": pack("eeee")}}
];

for (let i = 0; i < tokens.length; ++i) {
    const nextId = (await contract.storage())["next_token_id"].toString();

    console.log(`Minting token #${i} (id: ${nextId})…`);

    const send = await contract.methodsObject.mint(tokens[i]).send();

    console.log("Awaiting confirmation…");

    await send.confirmation();
}

console.log(await contract.tzip16().getMetadata())
